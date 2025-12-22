#!/usr/bin/env python3
# Copyright (c) 2025 The OpenSY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

"""
OpenSY Hashrate Monitor

Monitors network hashrate and alerts on significant drops that may indicate:
- Mining pool issues
- Network attacks
- RandomX/PoW algorithm problems requiring emergency fallback

Features:
- Configurable drop threshold (default 30%)
- Rolling average comparison
- Multiple alert methods (log, webhook, email)
- Historical tracking with CSV export
"""

import argparse
import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

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
            "id": "hashrate_monitor",
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
                    "footer": "OpenSY Hashrate Monitor",
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


class HashrateMonitor:
    """Monitors network hashrate and alerts on significant changes."""
    
    def __init__(
        self,
        rpc: RPCClient,
        alert_handler: AlertHandler,
        drop_threshold: float = 0.30,
        rise_threshold: float = 0.50,
        window_size: int = 10,
        history_file: str = None
    ):
        self.rpc = rpc
        self.alert_handler = alert_handler
        self.drop_threshold = drop_threshold
        self.rise_threshold = rise_threshold
        self.window_size = window_size
        self.history_file = history_file
        
        # State
        self.hashrate_history = []
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5 minutes between repeat alerts
        self.baseline_hashrate = None
    
    def get_hashrate(self, nblocks: int = 120) -> float:
        """Get current network hashrate (hashes per second)."""
        return float(self.rpc.call("getnetworkhashps", [nblocks]))
    
    def get_blockchain_info(self) -> dict:
        """Get current blockchain info."""
        return self.rpc.call("getblockchaininfo")
    
    def calculate_rolling_average(self) -> Optional[float]:
        """Calculate rolling average from history."""
        if len(self.hashrate_history) < self.window_size:
            return None
        recent = self.hashrate_history[-self.window_size:]
        return sum(recent) / len(recent)
    
    def format_hashrate(self, hashrate: float) -> str:
        """Format hashrate with appropriate unit."""
        units = [
            (1e18, "EH/s"),
            (1e15, "PH/s"),
            (1e12, "TH/s"),
            (1e9, "GH/s"),
            (1e6, "MH/s"),
            (1e3, "KH/s"),
            (1, "H/s")
        ]
        for threshold, unit in units:
            if hashrate >= threshold:
                return f"{hashrate / threshold:.2f} {unit}"
        return f"{hashrate:.2f} H/s"
    
    def check_hashrate(self) -> dict:
        """Check current hashrate and compare to baseline/average."""
        try:
            current = self.get_hashrate()
            blockchain = self.get_blockchain_info()
            
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "height": blockchain.get("blocks", 0),
                "hashrate": current,
                "hashrate_formatted": self.format_hashrate(current),
                "alert": None
            }
            
            # Add to history
            self.hashrate_history.append(current)
            if len(self.hashrate_history) > 1000:
                self.hashrate_history = self.hashrate_history[-500:]
            
            # Set baseline from first reading
            if self.baseline_hashrate is None:
                self.baseline_hashrate = current
                logger.info(f"Baseline hashrate set: {self.format_hashrate(current)}")
                return result
            
            # Calculate rolling average
            avg = self.calculate_rolling_average()
            if avg is None:
                return result
            
            result["rolling_average"] = avg
            result["rolling_average_formatted"] = self.format_hashrate(avg)
            
            # Check for significant drop
            drop_pct = (avg - current) / avg if avg > 0 else 0
            rise_pct = (current - avg) / avg if avg > 0 else 0
            
            result["change_pct"] = -drop_pct if drop_pct > 0 else rise_pct
            
            now = time.time()
            
            if drop_pct >= self.drop_threshold:
                severity = "critical" if drop_pct >= 0.50 else "warning"
                result["alert"] = {
                    "type": "hashrate_drop",
                    "severity": severity,
                    "drop_pct": drop_pct * 100
                }
                
                if now - self.last_alert_time > self.alert_cooldown:
                    self.alert_handler.send_alert(
                        title=f"Hashrate Drop: {drop_pct*100:.1f}%",
                        message=(
                            f"Network hashrate has dropped significantly!\n\n"
                            f"Current: {self.format_hashrate(current)}\n"
                            f"Average: {self.format_hashrate(avg)}\n"
                            f"Drop: {drop_pct*100:.1f}%\n"
                            f"Block Height: {result['height']}\n\n"
                            f"Possible causes:\n"
                            f"• Mining pool offline\n"
                            f"• Network partition\n"
                            f"• PoW algorithm attack\n\n"
                            f"Action: Investigate immediately. If RandomX is compromised, "
                            f"consider emergency Argon2id activation."
                        ),
                        severity=severity
                    )
                    self.last_alert_time = now
            
            elif rise_pct >= self.rise_threshold:
                result["alert"] = {
                    "type": "hashrate_spike",
                    "severity": "warning",
                    "rise_pct": rise_pct * 100
                }
                
                if now - self.last_alert_time > self.alert_cooldown:
                    self.alert_handler.send_alert(
                        title=f"Hashrate Spike: +{rise_pct*100:.1f}%",
                        message=(
                            f"Network hashrate spiked significantly!\n\n"
                            f"Current: {self.format_hashrate(current)}\n"
                            f"Average: {self.format_hashrate(avg)}\n"
                            f"Rise: +{rise_pct*100:.1f}%\n"
                            f"Block Height: {result['height']}\n\n"
                            f"Possible causes:\n"
                            f"• New mining pool joined\n"
                            f"• Potential 51% attack preparation\n"
                            f"• Market conditions (price increase)"
                        ),
                        severity="warning"
                    )
                    self.last_alert_time = now
            
            # Save to history file
            if self.history_file:
                self._save_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking hashrate: {e}")
            return {"error": str(e)}
    
    def _save_history(self, result: dict):
        """Append result to CSV history file."""
        try:
            file_exists = os.path.exists(self.history_file)
            with open(self.history_file, "a") as f:
                if not file_exists:
                    f.write("timestamp,height,hashrate,rolling_avg,change_pct,alert_type\n")
                f.write(
                    f"{result['timestamp']},"
                    f"{result.get('height', '')},"
                    f"{result.get('hashrate', '')},"
                    f"{result.get('rolling_average', '')},"
                    f"{result.get('change_pct', '')*100 if result.get('change_pct') else ''},"
                    f"{result.get('alert', {}).get('type', '') if result.get('alert') else ''}\n"
                )
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def run(self, interval: int = 60):
        """Run continuous monitoring loop."""
        logger.info(f"Starting hashrate monitor (interval: {interval}s, drop threshold: {self.drop_threshold*100}%)")
        
        while True:
            result = self.check_hashrate()
            
            if "error" not in result:
                status = "🟢" if not result.get("alert") else "🔴"
                change = result.get("change_pct", 0) * 100
                change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
                
                logger.info(
                    f"{status} Height: {result.get('height', '?'):,} | "
                    f"Hashrate: {result.get('hashrate_formatted', '?')} | "
                    f"Change: {change_str}"
                )
            
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="OpenSY Network Hashrate Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic monitoring
  python3 hashrate_monitor.py --rpc-user user --rpc-password pass

  # With webhook alerts (Slack/Discord)
  python3 hashrate_monitor.py --rpc-user user --rpc-password pass \\
      --webhook-url https://hooks.slack.com/services/XXX

  # Custom thresholds
  python3 hashrate_monitor.py --rpc-user user --rpc-password pass \\
      --drop-threshold 0.20 --interval 30
"""
    )
    
    # RPC connection
    parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host (default: 127.0.0.1)")
    parser.add_argument("--rpc-port", type=int, default=9632, help="RPC port (default: 9632)")
    parser.add_argument("--rpc-user", required=True, help="RPC username")
    parser.add_argument("--rpc-password", required=True, help="RPC password")
    
    # Monitoring settings
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--drop-threshold", type=float, default=0.30, help="Alert threshold for drops (default: 0.30 = 30%%)")
    parser.add_argument("--rise-threshold", type=float, default=0.50, help="Alert threshold for spikes (default: 0.50 = 50%%)")
    parser.add_argument("--window-size", type=int, default=10, help="Rolling average window (default: 10)")
    
    # Alerting
    parser.add_argument("--webhook-url", help="Slack/Discord webhook URL for alerts")
    parser.add_argument("--history-file", help="CSV file to save hashrate history")
    
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
    monitor = HashrateMonitor(
        rpc=rpc,
        alert_handler=alert_handler,
        drop_threshold=args.drop_threshold,
        rise_threshold=args.rise_threshold,
        window_size=args.window_size,
        history_file=args.history_file
    )
    
    try:
        monitor.run(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
