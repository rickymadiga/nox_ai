import os
import importlib
import traceback
import logging

logger = logging.getLogger(__name__)


def load_plugins(runtime, plugins_path="plugins"):
    """Load all plugins from the plugins directory"""

    # ✅ STEP 1: REGISTER LILY FIRST
    try:
        from orchestrator.lily import register as register_lily
        register_lily(runtime)
        logger.info("[CORE] ✅ Lily registered")
        print("[CORE] ✅ Lily registered")
    except Exception as e:
        logger.error(f"[CORE ERROR] Failed to register Lily: {e}", exc_info=True)
        print(f"[CORE ERROR] Failed to register Lily: {e}")
        traceback.print_exc()

    # ================================
    # STEP 2: LOAD PLUGINS DYNAMICALLY
    # ================================
    if not os.path.exists(plugins_path):
        logger.warning(f"[PLUGIN LOADER] plugins folder not found at {plugins_path}")
        print(f"[PLUGIN LOADER] plugins folder not found at {plugins_path}")
        return

    loaded_count = 0
    for folder in os.listdir(plugins_path):
        plugin_dir = os.path.join(plugins_path, folder)

        # Skip non-directories
        if not os.path.isdir(plugin_dir):
            continue

        # Skip hidden/junk folders
        if folder.startswith("__") or folder.startswith("."):
            continue

        try:
            # Build module path: plugins.research_agent.plugin
            module_path = f"{plugins_path}.{folder}.plugin"

            # Check if plugin.py exists
            plugin_file = os.path.join(plugin_dir, "plugin.py")
            if not os.path.exists(plugin_file):
                logger.debug(f"[PLUGIN SKIP] {folder} (no plugin.py)")
                print(f"[PLUGIN SKIP] {folder} (no plugin.py)")
                continue

            # Import the plugin module
            logger.info(f"[PLUGIN] Importing {module_path}...")
            module = importlib.import_module(module_path)

            # Check if it has a register function
            if not hasattr(module, "register"):
                logger.warning(f"[PLUGIN SKIP] {folder} (missing register())")
                print(f"[PLUGIN SKIP] {folder} (missing register())")
                continue

            # Call the register function
            logger.info(f"[PLUGIN] Calling register() for {folder}...")
            module.register(runtime)
            
            logger.info(f"[PLUGIN] ✅ Loaded {folder}")
            print(f"[PLUGIN] ✅ Loaded {folder}")
            loaded_count += 1

        except ModuleNotFoundError as e:
            logger.error(f"[PLUGIN ERROR] {folder}: Module not found: {e}")
            print(f"[PLUGIN ERROR] {folder}: Module not found: {e}")
            traceback.print_exc()
        except Exception as e:
            logger.error(f"[PLUGIN ERROR] {folder}: {e}", exc_info=True)
            print(f"[PLUGIN ERROR] {folder}: {e}")
            traceback.print_exc()

    logger.info(f"[PLUGIN LOADER] ✅ Loaded {loaded_count} plugins")
    print(f"[PLUGIN LOADER] ✅ Loaded {loaded_count} plugins")