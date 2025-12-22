#!/usr/bin/env python3
# Copyright (c) 2025 The OpenSY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

"""
OpenSY Block Time Monitor

Monitors block arrival times and alerts on anomalies that may indicate:
- Mining issues (slow blocks)
- Network attacks (rapid blocks, selfish mining)
- PoW algorithm problems

Features:
- Real-time block time tracking
- Alerts on abnormal block gaps (too slow or too fast)
- Reorg detection
- Block time distribution analysis
- Multiple alert methods (log, webhook, email)
"""

import argparse
import json
import logging
import os
import smtplib
import sys
import time
from collections import deque
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional, List, Dict

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip3 install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# OpenSY target block time (10 minutes = 600 seconds)
TARGET_BLOCK_TIME = 600


class RPCClient:
    """Simple JSON-RPC client for opensyd."""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.url = f"http://{host}:{port}"
        self.auth = (user, password)
        self.headers = {"Content-Type": "application/json"}
    
    def call(self, method: str, params: list = None) -> dict:
        """Execute an RPC call."""
        payload = {
            "jsonrpc": "2.0",
            "id": "blocktime_monitor",
            "method": method,
            "params": params or []
        }
        try:
            response = requests.post(
                self.url,
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result and result["error"]:
                raise Exception(f"RPC error: {result['error']}")
            return result.get("result")
        except requests.exceptions.RequestException as e:
            raise Exception(f"RPC connection failed: {e}")


class AlertHandler:
    """Handles alerting via multiple channels."""
    
    def __init__(self, webhook_url: str = None, email_config: dict = None):
        self.webhook_url = webhook_url
        self.email_config = email_config
    
    def send_alert(self, title: str, message: str, severity: str = "warning"):
        """Send alert via all configured channels."""
        # Always log
        log_func = logger.warning if severity == "warning" else logger.critical
        log_func(f"🚨 ALERT: {title}\n{message}")
        
        # Webhook (Slack, Discord, etc.)
        if self.webhook_url:
            self._send_webhook(title, message, severity)
        
        # Email
        if self.email_config:
            self._send_email(title, message, severity)
    
    def _send_webhook(self, title: str, message: str, severity: str):
        """Send alert to webhook (Slack/Discord compatible)."""
        try:
            color = "#ff0000" if severity == "critical" else "#ffaa00"
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"🚨 OpenSY Alert: {title}",
                    "text": message,
                    "footer": "OpenSY Block Time Monitor",
                    "ts": int(time.time())
                }]
            }
            requests.post(self.webhook_url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")
    
    def _send_email(self, title: str, message: str, severity: str):
        """Send alert via email."""
        try:
            msg = MIMEText(message)
            msg["Subject"] = f"[OpenSY {severity.upper()}] {title}"
            msg["From"] = self.email_config["from"]
            msg["To"] = self.email_config["to"]
            
            with smtplib.SMTP(self.email_config["smtp_host"], self.email_config.get("smtp_port", 587)) as server:
                server.starttls()
                if self.email_config.get("smtp_user"):
                    server.login(self.email_config["smtp_user"], self.email_config["smtp_password"])
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Email alert failed: {e}")


class BlockTimeMonitor:
    """Monitors block times and detects anomalies."""
    
    def __init__(
        self,
        rpc: RPCClient,
        alert_handler: AlertHandler,
        slow_threshold: float = 3.0,  # Alert if block takes 3x target time
        fast_threshold: float = 0.1,  # Alert if 10 blocks in <10% expected time
        reorg_depth_alert: int = 3,   # Alert on reorgs deeper than this
        history_file: str = None
    ):
        self.rpc = rpc
        self.alert_handler = alert_handler
        self.slow_threshold = slow_threshold
        self.fast_threshold = fast_threshold
        self.reorg_depth_alert = reorg_depth_alert
        self.history_file = history_file
        
        # State
        self.last_height = 0
        self.last_hash = None
        self.last_block_time = None
        self.block_times = deque(maxlen=100)  # Recent block times
        self.last_alert_time = {}  # Per-alert-type cooldowns
        self.alert_cooldown = 300  # 5 minutes between repeat alerts
        
        # Statistics
        self.blocks_seen = 0
        self.reorgs_detected = 0
        self.slow_blocks = 0
        self.fast_sequences = 0
    
    def get_blockchain_info(self) -> dict:
        """Get current blockchain info."""
        return self.rpc.call("getblockchaininfo")
    
    def get_block_header(self, blockhash: str) -> dict:
        """Get block header by hash."""
        return self.rpc.call("getblockheader", [blockhash])
    
    def get_block_hash(self, height: int) -> str:
        """Get block hash at height."""
        return self.rpc.call("getblockhash", [height])
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def can_alert(self, alert_type: str) -> bool:
        """Check if we can send an alert (cooldown check)."""
        now = time.time()
        last = self.last_alert_time.get(alert_type, 0)
        if now - last > self.alert_cooldown:
            self.last_alert_time[alert_type] = now
            return True
        return False
    
    def analyze_block_time_distribution(self) -> Dict:
        """Analyze recent block time distribution."""
        if len(self.block_times) < 10:
            return {}
        
        times = list(self.block_times)
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Count blocks in different ranges
        fast = sum(1 for t in times if t < TARGET_BLOCK_TIME * 0.5)
        normal = sum(1 for t in times if TARGET_BLOCK_TIME * 0.5 <= t <= TARGET_BLOCK_TIME * 2)
        slow = sum(1 for t in times if t > TARGET_BLOCK_TIME * 2)
        
        return {
            "average": avg,
            "min": min_time,
            "max": max_time,
            "fast_count": fast,
            "normal_count": normal,
            "slow_count": slow,
            "sample_size": len(times)
        }
    
    def check_for_reorg(self, current_hash: str, current_height: int) -> Optional[int]:
        """Check if a reorg occurred. Returns reorg depth or None."""
        if self.last_height == 0:
            return None
        
        # Height went down = definite reorg
        if current_height < self.last_height:
            return self.last_height - current_height
        
        # Height same but hash different = reorg at tip
        if current_height == self.last_height and current_hash != self.last_hash:
            return 1
        
        # Height advanced - check if previous block is what we expected
        if current_height == self.last_height + 1:
            try:
                header = self.get_block_header(current_hash)
                if header.get("previousblockhash") != self.last_hash:
                    # Previous block changed = reorg happened
                    # Find common ancestor
                    depth = 1
                    check_height = self.last_height
                    while depth < 100:  # Limit search
                        try:
                            expected_hash = self.get_block_hash(check_height)
                            # We can't easily verify without storing more history
                            # For now, just report shallow reorg
                            return depth
                        except:
                            break
                        depth += 1
            except:
                pass
        
        return None
    
    def process_new_block(self, height: int, blockhash: str) -> Dict:
        """Process a new block and check for anomalies."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "height": height,
            "hash": blockhash[:16] + "...",
            "alerts": []
        }
        
        try:
            header = self.get_block_header(blockhash)
            block_time = header.get("time", 0)
            
            # Calculate time since last block
            if self.last_block_time:
                time_delta = block_time - self.last_block_time
                result["block_time"] = time_delta
                result["block_time_formatted"] = self.format_duration(time_delta)
                
                # Record for statistics
                if time_delta > 0:
                    self.block_times.append(time_delta)
                
                # Check for slow block
                slow_limit = TARGET_BLOCK_TIME * self.slow_threshold
                if time_delta > slow_limit:
                    self.slow_blocks += 1
                    result["alerts"].append({
                        "type": "slow_block",
                        "severity": "warning" if time_delta < slow_limit * 2 else "critical",
                        "block_time": time_delta,
                        "threshold": slow_limit
                    })
                    
                    if self.can_alert("slow_block"):
                        severity = "warning" if time_delta < slow_limit * 2 else "critical"
                        self.alert_handler.send_alert(
                            title=f"Slow Block: {self.format_duration(time_delta)}",
                            message=(
                                f"Block took abnormally long to mine!\n\n"
                                f"Block Height: {height}\n"
                                f"Time Since Last: {self.format_duration(time_delta)}\n"
                                f"Expected: ~{self.format_duration(TARGET_BLOCK_TIME)}\n"
                                f"Threshold: {self.format_duration(slow_limit)}\n\n"
                                f"Possible causes:\n"
                                f"• Hashrate drop (check hashrate_monitor)\n"
                                f"• Mining pool issues\n"
                                f"• Network difficulty too high\n"
                                f"• Bad luck (normal variance)"
                            ),
                            severity=severity
                        )
                
                # Check for rapid block sequence
                if len(self.block_times) >= 10:
                    last_10 = list(self.block_times)[-10:]
                    total_time = sum(last_10)
                    expected_time = TARGET_BLOCK_TIME * 10
                    
                    if total_time < expected_time * self.fast_threshold:
                        self.fast_sequences += 1
                        result["alerts"].append({
                            "type": "rapid_blocks",
                            "severity": "critical",
                            "total_time": total_time,
                            "expected": expected_time
                        })
                        
                        if self.can_alert("rapid_blocks"):
                            self.alert_handler.send_alert(
                                title="Rapid Block Sequence Detected!",
                                message=(
                                    f"10 blocks mined in unusually short time!\n\n"
                                    f"Current Height: {height}\n"
                                    f"Time for 10 blocks: {self.format_duration(total_time)}\n"
                                    f"Expected: ~{self.format_duration(expected_time)}\n\n"
                                    f"⚠️ POTENTIAL ATTACK INDICATORS:\n"
                                    f"• Selfish mining attack\n"
                                    f"• Time-warp attack\n"
                                    f"• Massive hashrate increase\n\n"
                                    f"Action: Investigate immediately!"
                                ),
                                severity="critical"
                            )
            
            # Check for reorg
            reorg_depth = self.check_for_reorg(blockhash, height)
            if reorg_depth and reorg_depth >= self.reorg_depth_alert:
                self.reorgs_detected += 1
                result["alerts"].append({
                    "type": "reorg",
                    "severity": "critical" if reorg_depth >= 6 else "warning",
                    "depth": reorg_depth
                })
                
                if self.can_alert("reorg"):
                    severity = "critical" if reorg_depth >= 6 else "warning"
                    self.alert_handler.send_alert(
                        title=f"Chain Reorganization: {reorg_depth} blocks",
                        message=(
                            f"Blockchain reorganization detected!\n\n"
                            f"Reorg Depth: {reorg_depth} blocks\n"
                            f"New Tip Height: {height}\n"
                            f"New Tip Hash: {blockhash[:32]}...\n\n"
                            f"{'⚠️ DEEP REORG - Possible 51% attack!' if reorg_depth >= 6 else 'Shallow reorg - likely normal.'}\n\n"
                            f"Action: Monitor for follow-up reorgs."
                        ),
                        severity=severity
                    )
            
            # Update state
            self.last_height = height
            self.last_hash = blockhash
            self.last_block_time = block_time
            self.blocks_seen += 1
            
            # Add distribution stats
            dist = self.analyze_block_time_distribution()
            if dist:
                result["distribution"] = dist
            
            # Save history
            if self.history_file:
                self._save_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing block {height}: {e}")
            return {"error": str(e)}
    
    def _save_history(self, result: dict):
        """Append result to CSV history file."""
        try:
            file_exists = os.path.exists(self.history_file)
            with open(self.history_file, "a") as f:
                if not file_exists:
                    f.write("timestamp,height,block_time,alert_types\n")
                alert_types = ",".join(a["type"] for a in result.get("alerts", []))
                f.write(
                    f"{result['timestamp']},"
                    f"{result.get('height', '')},"
                    f"{result.get('block_time', '')},"
                    f"{alert_types}\n"
                )
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def run(self, interval: int = 10):
        """Run continuous monitoring loop."""
        logger.info(f"Starting block time monitor (check interval: {interval}s)")
        logger.info(f"Thresholds: slow={self.slow_threshold}x, fast={self.fast_threshold}, reorg_depth={self.reorg_depth_alert}")
        
        while True:
            try:
                info = self.get_blockchain_info()
                current_height = info.get("blocks", 0)
                current_hash = info.get("bestblockhash", "")
                
                # Check if new block(s)
                if current_height > self.last_height or current_hash != self.last_hash:
                    # Process any skipped blocks
                    if self.last_height > 0 and current_height > self.last_height + 1:
                        for h in range(self.last_height + 1, current_height):
                            try:
                                block_hash = self.get_block_hash(h)
                                self.process_new_block(h, block_hash)
                            except:
                                pass
                    
                    # Process current block
                    result = self.process_new_block(current_height, current_hash)
                    
                    # Log status
                    status = "🟢" if not result.get("alerts") else "🔴"
                    block_time_str = result.get("block_time_formatted", "?")
                    alert_str = f" | Alerts: {len(result.get('alerts', []))}" if result.get("alerts") else ""
                    
                    logger.info(
                        f"{status} Block {current_height:,} | "
                        f"Time: {block_time_str}{alert_str}"
                    )
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="OpenSY Block Time Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic monitoring
  python3 blocktime_monitor.py --rpc-user user --rpc-password pass

  # With webhook alerts
  python3 blocktime_monitor.py --rpc-user user --rpc-password pass \\
      --webhook-url https://hooks.slack.com/services/XXX

  # Custom thresholds
  python3 blocktime_monitor.py --rpc-user user --rpc-password pass \\
      --slow-threshold 2.5 --reorg-depth 2
"""
    )
    
    # RPC connection
    parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host (default: 127.0.0.1)")
    parser.add_argument("--rpc-port", type=int, default=9632, help="RPC port (default: 9632)")
    parser.add_argument("--rpc-user", required=True, help="RPC username")
    parser.add_argument("--rpc-password", required=True, help="RPC password")
    
    # Monitoring settings
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds (default: 10)")
    parser.add_argument("--slow-threshold", type=float, default=3.0, help="Alert if block takes Nx target time (default: 3.0)")
    parser.add_argument("--fast-threshold", type=float, default=0.10, help="Alert if 10 blocks in <N%% expected time (default: 0.10)")
    parser.add_argument("--reorg-depth", type=int, default=3, help="Alert on reorgs deeper than N blocks (default: 3)")
    
    # Alerting
    parser.add_argument("--webhook-url", help="Slack/Discord webhook URL for alerts")
    parser.add_argument("--history-file", help="CSV file to save block time history")
    
    # Email alerting (optional)
    parser.add_argument("--email-to", help="Email address for alerts")
    parser.add_argument("--email-from", help="From email address")
    parser.add_argument("--smtp-host", help="SMTP server host")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP port (default: 587)")
    parser.add_argument("--smtp-user", help="SMTP username")
    parser.add_argument("--smtp-password", help="SMTP password")
    
    args = parser.parse_args()
    
    # Setup RPC client
    rpc = RPCClient(args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password)
    
    # Setup alerting
    email_config = None
    if args.email_to and args.smtp_host:
        email_config = {
            "to": args.email_to,
            "from": args.email_from or args.email_to,
            "smtp_host": args.smtp_host,
            "smtp_port": args.smtp_port,
            "smtp_user": args.smtp_user,
            "smtp_password": args.smtp_password
        }
    
    alert_handler = AlertHandler(
        webhook_url=args.webhook_url,
        email_config=email_config
    )
    
    # Setup and run monitor
    monitor = BlockTimeMonitor(
        rpc=rpc,
        alert_handler=alert_handler,
        slow_threshold=args.slow_threshold,
        fast_threshold=args.fast_threshold,
        reorg_depth_alert=args.reorg_depth,
        history_file=args.history_file
    )
    
    try:
        monitor.run(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        logger.info(f"Stats: {monitor.blocks_seen} blocks, {monitor.reorgs_detected} reorgs, "
                   f"{monitor.slow_blocks} slow, {monitor.fast_sequences} fast sequences")
        sys.exit(0)


if __name__ == "__main__":
    main()
