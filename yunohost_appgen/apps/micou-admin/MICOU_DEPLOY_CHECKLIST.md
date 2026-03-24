# Micou packaging checklist for micou-admin

1. Confirm that the runtime, URL strategy, storage path, and authentication model are stable enough to package.
2. Review all seven official App Generator sections in `streamlined` mode and fill missing values before generation.
3. Generate the official YunoHost package skeleton with the same answers recorded in `appgen_answers.json`.
4. Complete DESCRIPTION.md, ADMIN.md, and any PRE_INSTALL.md or POST_INSTALL.md notes required by the service.
5. Test install, upgrade, backup, restore, and remove flows.
6. Install the package on a YunoHost host and confirm the tile, permission, and route behave as expected.
7. Update the micou service registry entry and YunoHost access state after the install.
8. Run the control-plane sync so PostgreSQL, grants, portal visibility, and the registry converge on the same state.
