# VPN Setup Guide

Presidio uses **Cisco AnyConnect** for secure remote access.

## How to set up the VPN

1. Open the Software Center (Windows) or Self Service (macOS) and install
   **Cisco AnyConnect Secure Mobility Client**.
2. Launch AnyConnect and enter the server address: `vpn.presidio.internal`.
3. Sign in with your corporate SSO credentials.
4. Approve the multi-factor authentication (MFA) prompt on your phone.
5. Once connected, the AnyConnect icon shows a lock indicating an active tunnel.

## Notes

- VPN access is required when working from outside the office network to reach
  internal systems (Jira, Confluence, file shares).
- If MFA fails, re-register your device at `https://mfa.presidio.internal`.
- For connection issues, contact the IT Service Desk at ext. 4357 (HELP).
