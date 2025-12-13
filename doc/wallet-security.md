# Wallet Security and Password Guidelines

**Version:** 1.0  
**Date:** December 2025

---

## Overview

This guide provides best practices for securing your OpenSY wallet and choosing strong encryption passphrases. Following these guidelines helps protect your funds from theft and loss.

---

## Understanding Wallet Encryption

### How It Works

When you encrypt your wallet with `encryptwallet`, OpenSY:

1. Derives an encryption key from your passphrase using a Key Derivation Function (KDF)
2. Encrypts all private keys using AES-256
3. Stores only the encrypted keys on disk

Without your passphrase, the private keys cannot be recovered—even by the developers.

### Key Derivation Methods

OpenSY supports two key derivation methods:

| Method | Algorithm | Security Level | Notes |
|--------|-----------|----------------|-------|
| **0** | SHA512 (Legacy) | Good | Compatible with older wallets |
| **1** | Argon2id | Excellent | Memory-hard, GPU/ASIC resistant |

**New wallets use Argon2id by default** for better protection against brute-force attacks.

---

## Choosing a Strong Passphrase

### Minimum Requirements

- **Length:** At least 12 characters (16+ recommended)
- **Complexity:** Mix of uppercase, lowercase, numbers, and symbols
- **Uniqueness:** Never reuse passwords from other services

### Recommended Approaches

#### Option 1: Passphrase (Recommended)

Use 4-6 random words with separators:

```
correct-horse-battery-staple-pyramid
volcano.umbrella.seventeen.rainbow.jazz
```

This is easier to remember and type than random characters, while being very secure.

#### Option 2: Random Password

Use a password manager to generate:

```
K#9mP$2xL@nQ7wR!vE4
```

Store this securely in your password manager.

#### Option 3: Sentence-Based

Create a memorable sentence and use first letters:

```
"I bought my first Bitcoin in January 2015 for $200!"
→ IbmfBiJ2f$2!
```

### What NOT to Do

❌ **Personal Information:**
- Your name, birthday, address, phone number
- Pet names, family member names
- Social media usernames

❌ **Common Patterns:**
- Dictionary words alone (`password`, `opensy`)
- Keyboard patterns (`qwerty`, `123456`)
- Repeated characters (`aaaa`, `1111`)
- Simple substitutions (`p@ssw0rd`)

❌ **Reused Passwords:**
- Never use a password that's used anywhere else
- If one service is breached, all your accounts are at risk

---

## Password Storage

### Do's

✅ **Password Manager:** Use a reputable password manager:
- Bitwarden (open source)
- 1Password
- KeePassXC (offline)

✅ **Paper Backup:** Store a written copy in a safe or safety deposit box

✅ **Multiple Locations:** Keep encrypted backups in 2+ physical locations

### Don'ts

❌ **Plain Text Files:** Never store passwords in unencrypted files

❌ **Cloud Storage:** Avoid storing passwords in unencrypted cloud services

❌ **Shared Documents:** Never share your password via email, text, or chat

---

## Wallet Security Best Practices

### Backup Your Wallet

After encrypting your wallet, immediately backup:

```bash
opensy-cli backupwallet "/path/to/backup/wallet-backup.dat"
```

Store backups in multiple secure locations:
- Encrypted USB drive in a safe
- Bank safety deposit box
- Secure cloud storage (additional encryption recommended)

### Wallet Isolation

For significant holdings, consider:

1. **Hardware Wallet:** Use a dedicated hardware device
2. **Cold Storage:** Keep majority of funds in offline wallet
3. **Separate Hot Wallet:** Only keep spending funds in online wallet

### Environment Security

- Keep your operating system and OpenSY software updated
- Use full-disk encryption on your computer
- Run antivirus/antimalware software
- Be cautious with browser extensions and downloads

---

## Recovery Procedures

### Lost Passphrase

**There is no recovery mechanism.** If you lose your passphrase:

- Your funds are permanently inaccessible
- No one can help you recover access
- This is by design—it protects you from attackers

**Prevention:**
- Store passphrase backups in multiple secure locations
- Test your backup by unlocking your wallet periodically

### Wallet Corruption

If your wallet file becomes corrupted:

1. Try restoring from your backup:
   ```bash
   # Stop opensyd first
   cp /path/to/backup/wallet-backup.dat ~/.opensy/wallets/default/wallet.dat
   ```

2. If backup is also corrupted, you may need the wallet descriptor backup

### Checking Encryption Status

To verify your wallet is encrypted:

```bash
opensy-cli getwalletinfo | grep unlocked_until
```

- If this field exists, your wallet is encrypted
- A value of `0` means it's locked
- A positive value is the unlock expiration timestamp

---

## Upgrading Wallet Encryption

If your wallet uses the legacy SHA512 derivation (method 0), you can upgrade to Argon2id for better security:

**Current Status Check:**
Your wallet info doesn't directly expose the derivation method, but if your wallet was created before [version with Argon2id], it uses SHA512.

**Upgrade Process (Future Release):**
The `upgradewalletencryption` RPC will allow in-place upgrade to Argon2id. Until then:

1. Create a new wallet (will use Argon2id by default)
2. Transfer funds from old wallet to new wallet
3. Backup the new wallet
4. Securely delete the old wallet

---

## Security Checklist

Before storing significant funds:

- [ ] Wallet is encrypted (`getwalletinfo` shows `unlocked_until`)
- [ ] Passphrase is 12+ characters with high complexity
- [ ] Passphrase is stored in secure password manager
- [ ] Paper backup of passphrase exists in secure location
- [ ] Wallet backup created after encryption
- [ ] Backup tested by restoring to a test environment
- [ ] Operating system is up to date
- [ ] Full-disk encryption is enabled
- [ ] Antivirus software is running and current

---

## Emergency Contacts

If you suspect your wallet has been compromised:

1. **Do not send transactions** - the attacker may be monitoring
2. **Transfer funds** to a new, secure wallet immediately
3. **Report** to security@opensy.org if you believe it's a software issue
4. **Document** everything for potential investigation

---

## Frequently Asked Questions

**Q: Can OpenSY developers recover my passphrase?**
A: No. Encryption is done locally. We never have access to your passphrase.

**Q: How often should I change my wallet passphrase?**
A: Only if you suspect it may have been compromised. Frequent changes increase the risk of losing access.

**Q: Is 8 characters enough?**
A: No. Modern attacks can crack 8-character passwords quickly. Use 12+ characters minimum.

**Q: Should I use special characters?**
A: Yes, if using a random password. For passphrases, length matters more than special characters.

**Q: Can I encrypt an existing wallet?**
A: Yes, use `encryptwallet "your passphrase"`. This generates a new HD seed, so backup immediately after.

---

*Last updated: December 2025*
