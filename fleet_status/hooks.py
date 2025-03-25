
def pre_init_hook(env):
    """Delete All Records in fleet status."""
    env.cr.execute("""DELETE FROM fleet_vehicle_state;""")

