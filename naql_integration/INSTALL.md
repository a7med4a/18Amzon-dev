# Naql Integration Module Installation Guide

## Quick Installation Steps

1. **Copy Module Files**
   ```bash
   cp -r sta_integration_module /opt/odoo/custom-addons/
   chown -R odoo:odoo /opt/odoo/custom-addons/sta_integration_module
   ```

2. **Restart Odoo Service**
   ```bash
   sudo systemctl restart odoo
   ```

3. **Update Apps List**
   - Go to Apps menu in Odoo
   - Click "Update Apps List"

4. **Install Module**
   - Search for "Naql Integration"
   - Click "Install"

5. **Configure Settings**
   - Go to Settings > Naql Integration
   - Enter your Naql credentials
   - Test connection

## Required Dependencies

Make sure these modules are installed first:
- rental_contract
- branches_management
- customer_info
- vehicle_info
- fleet_status

## Configuration Checklist

- [ ] Naql App ID configured
- [ ] Naql App Key configured
- [ ] Authorization Token configured
- [ ] Connection test successful
- [ ] Branches synchronized
- [ ] Rent policies synchronized
- [ ] Local branches mapped

## Support

For installation support, please refer to the main documentation or contact technical support.

