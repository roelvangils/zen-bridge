# Inspekt - Security Features

This document explains the security model implemented in Inspekt extensions (both Chrome and Firefox).

## Overview

To address concerns about arbitrary code execution and improve Chrome Web Store acceptance chances, we've implemented a comprehensive opt-in permission system.

## Explicit Domain Permission System

### How It Works

1. **First Visit to Any Domain**
   - Content script loads but does NOT connect to WebSocket
   - Permission check runs automatically
   - If domain not allowed: Beautiful modal appears

2. **Permission Modal**
   - Clear heading: "Inspekt - Allow CLI control of this website?"
   - Shows the domain name prominently
   - Lists what Zen Bridge will be able to do
   - Warning about only allowing trusted sites
   - Two buttons: "Deny" or "Allow [domain]"

3. **After Permission Granted**
   - Domain saved to `chrome.storage.sync` (syncs across devices)
   - WebSocket connection established
   - Zen commands now work on this domain
   - Permission persists across browser sessions

4. **Domain Management**
   - Extension popup shows all allowed domains
   - Current domain status highlighted
   - One-click to allow/remove domains
   - Full transparency - see everywhere Zen has access

### User Experience Flow

```
User visits github.com
    ↓
Content script loads
    ↓
Checks: Is github.com allowed?
    ↓ NO
Shows permission modal
    ↓
User clicks "Allow github.com"
    ↓
Domain saved to storage
    ↓
WebSocket connects
    ↓
✓ Zen commands work
```

### Subsequent Visits

```
User visits github.com again
    ↓
Content script loads
    ↓
Checks: Is github.com allowed?
    ↓ YES (already in storage)
WebSocket connects immediately
    ↓
✓ Zen commands work (no modal)
```

## Storage

**Location**: `chrome.storage.sync` (or `browser.storage.sync` for Firefox)

**Key**: `zen_allowed_domains`

**Value**: Array of allowed domain strings

**Example**:
```json
{
  "zen_allowed_domains": [
    "github.com",
    "gmail.com",
    "localhost",
    "example.com"
  ]
}
```

**Syncing**: Permissions sync across all devices where user is signed in to Chrome/Firefox

## Privacy & Data

### What We Store
- List of domains you've explicitly allowed
- Stored locally using browser's storage API
- Synced across your devices (via browser sync)

### What We DON'T Store
- No URLs or page content
- No browsing history
- No commands you run
- No personal information
- No analytics or tracking data

### Data Flow
```
Browser ←→ Extension ←→ localhost:8766 ←→ Your CLI

NO external servers
NO cloud services
NO data collection
```

## Security Benefits

### 1. Prevents Unauthorized Access
- Malicious websites can't automatically connect
- You must explicitly allow each domain
- No surprise connections

### 2. Least Privilege Principle
- Extension has permissions for `<all_urls>`
- But ONLY activates on domains you allow
- Unused permissions remain dormant

### 3. Transparent & Auditable
- See all allowed domains in popup
- Revoke access anytime
- Clear indication when Zen is active

### 4. User Control
- You decide which sites are safe
- No blanket trust required
- Fine-grained control per domain

## Implementation Details

### Files Involved

**`permissions.js`** (Content Script)
- Handles domain permission checks
- Shows opt-in modal
- Manages storage operations
- Loaded before main content script

**`content.js`** (Content Script)
- Checks permission before connecting
- Only establishes WebSocket if allowed
- Respects user's permission decisions

**`popup.html/js/css`** (Extension Popup)
- Displays current domain status
- Lists all allowed domains
- Allows adding/removing permissions
- Visual management interface

**`manifest.json`**
- Added `storage` permission
- Loads `permissions.js` before `content.js`

### Key Functions

```javascript
// Check if domain is allowed
ZenPermissions.isAllowed(domain)

// Show opt-in modal and wait for user decision
ZenPermissions.checkAndRequest()

// Add domain to allowed list
ZenPermissions.allowDomain(domain)

// Remove domain from allowed list
ZenPermissions.removeDomain(domain)

// Get all allowed domains
ZenPermissions.getAllowedDomains()
```

## Chrome Web Store Benefits

This security model addresses Chrome Web Store's main concerns:

### 1. Arbitrary Code Execution
**Before**: Extension could execute code on any website automatically
**Now**: User must explicitly allow each domain first

### 2. Broad Permissions
**Before**: `<all_urls>` looked dangerous without safeguards
**Now**: Permission gated by user opt-in per domain

### 3. User Trust
**Before**: Users couldn't control where extension worked
**Now**: Full transparency and control

### 4. Security Disclosure
**Before**: Hard to explain security model
**Now**: Clear, visible permission system

## Permission Justification for Chrome Web Store

When submitting to Chrome Web Store, use this justification:

**storage**:
```
Required to store user's domain permissions. Users must explicitly allow
each domain before the extension can control it. This list of allowed
domains is stored locally using chrome.storage.sync.
```

**host_permissions (<all_urls>)**:
```
Required to inject the content script that displays the permission modal
on all websites. The content script only establishes a connection AFTER
the user explicitly allows the domain. Users maintain full control over
which domains the extension can access.
```

## User Documentation

### For End Users

**Q: Do I need to allow every website?**
A: No! Only allow websites you actively want to control via Zen CLI. Most users only need 5-10 domains.

**Q: What if I deny a domain by mistake?**
A: Open the extension popup, find the domain, and click "Allow This Domain". Or refresh the page to see the modal again.

**Q: Can I revoke access later?**
A: Yes! Click the extension icon, find the domain in the list, and click "Remove".

**Q: Do my permissions sync across computers?**
A: Yes, if you're signed in to Chrome/Firefox, your allowed domains sync automatically.

**Q: Is this safe?**
A: Yes! You explicitly control which websites Zen can access. Plus, all communication stays between your browser and local CLI (localhost). No external servers involved.

### For Developers

**Q: How do I test the permission modal?**
A: Clear storage (`chrome.storage.sync.clear()` in console) and refresh the page.

**Q: Can I pre-allow domains programmatically?**
A: No, this would defeat the security model. Users must click "Allow" in the modal.

**Q: Does this work offline?**
A: Yes, permissions are stored locally and don't require internet.

## Testing

### Manual Testing

1. **First Visit**:
   ```bash
   # Clear storage
   chrome.storage.sync.clear()

   # Visit new domain
   # Modal should appear
   # Click "Allow"
   # WebSocket should connect
   ```

2. **Subsequent Visit**:
   ```bash
   # Visit same domain again
   # No modal (already allowed)
   # WebSocket connects automatically
   ```

3. **Popup Management**:
   ```bash
   # Open extension popup
   # Should show current domain
   # Should list all allowed domains
   # Click "Remove" on a domain
   # Refresh that domain's page
   # Modal should appear again
   ```

### Automated Testing

See `tests/permissions_test.js` (to be created) for automated permission tests.

## Future Enhancements

Possible improvements to consider:

1. **Temporary Permissions**
   - "Allow for this session only" option
   - Permission expires when browser closes

2. **Subdomain Control**
   - Option to allow entire domain vs. specific subdomain
   - Currently allows entire domain (e.g., *.github.com)

3. **Permission Groups**
   - Pre-defined groups (e.g., "Development Sites")
   - Bulk allow/remove

4. **Activity Log**
   - Show which domains were accessed when
   - Privacy-respecting local log

5. **Import/Export**
   - Export allowed domains to file
   - Import on different browser/profile

## Comparison with Other Extensions

How Zen Bridge's security compares to similar tools:

| Extension | Permission Model | Zen Bridge |
|-----------|------------------|------------|
| **Tampermonkey** | Per-script URL patterns | Per-domain opt-in |
| **Selenium IDE** | All URLs by default | Explicit opt-in required |
| **Puppeteer Recorder** | All URLs by default | Explicit opt-in required |
| **Chrome DevTools** | Built-in, always allowed | User-controlled |

**Advantage**: Zen Bridge gives users more control than most automation tools while maintaining full functionality.

## Compliance

This security model helps with:

- ✅ Chrome Web Store policies
- ✅ Firefox Add-ons policies
- ✅ GDPR (no personal data collected)
- ✅ User trust and transparency
- ✅ Enterprise security requirements

## Support

If users encounter issues with permissions:

1. Check extension popup for domain status
2. Verify domain is in allowed list
3. Try removing and re-adding the domain
4. Check browser console for errors
5. Report issues: https://github.com/roelvangils/zen-bridge/issues

---

**Last Updated**: 2024-11-11
**Version**: 4.0.0
**Applies To**: Both Chrome and Firefox extensions
