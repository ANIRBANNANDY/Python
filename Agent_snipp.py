def is_target_proc(proc, name_filter, cmd_filter=None):
    """Targets processes based solely on Name and Command Line content."""
    try:
        # 1. Check Process Name (Case Insensitive)
        if name_filter.lower() not in proc.name().lower():
            return False
            
        # 2. Check Command Line for specific string (e.g., "xyz" or filename)
        if cmd_filter:
            # Join command line list into a single string for searching
            cmdline_parts = proc.cmdline() if hasattr(proc, 'cmdline') else []
            cmdline_str = " ".join(cmdline_parts).lower()
            if cmd_filter.lower() not in cmdline_str:
                return False
                
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

def kill_sequence(filename):
    """
    Global cleanup on the server:
    1. Kills EVERY perl.exe that has 'xyz' in the command line.
    2. Kills EVERY sas.exe process found.
    3. Repeats 3 times with 5s delays.
    4. Deletes the specific file selected.
    """
    for attempt in range(3):
        found_any = False
        
        # --- PHASE 1: Kill all Perl with 'xyz' ---
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # Check if it's perl
                if proc.info['name'] and 'perl' in proc.info['name'].lower():
                    cmdline_str = " ".join(proc.info['cmdline'] or []).lower()
                    # Check if 'xyz' is in the command
                    if 'xyz' in cmdline_str:
                        proc.kill()
                        found_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # --- PHASE 2: Kill all SAS ---
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'sas.exe' in proc.info['name'].lower():
                    proc.kill()
                    found_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # If nothing was found to kill on the first try, we can likely stop
        if not found_any and attempt == 0:
            break
            
        # Wait 5 seconds before the next check/kill cycle
        time.sleep(5)

    # --- PHASE 3: Delete the specific file ---
    path = os.path.join(config['target_folder'], filename)
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        print(f"File deletion error: {e}")
        return False
        
    return True
