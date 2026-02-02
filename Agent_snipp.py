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
    Kills processes based on process name and command line segments.
    1. Targets Perl processes containing "xyz" and the filename.
    2. Targets all SAS.exe processes.
    """
    for attempt in range(3):
        found_active = False
        
        # --- PHASE 1: Kill Perl (Targeting "xyz" + filename) ---
        for proc in psutil.process_iter(['name', 'cmdline']):
            if is_target_proc(proc, "perl", "xyz"):
                cmdline_full = " ".join(proc.info['cmdline'] or "").lower()
                if filename.lower() in cmdline_full:
                    try:
                        proc.kill() # Direct kill for speed
                        found_active = True
                    except: pass

        # --- PHASE 2: Kill SAS (Global Target) ---
        for proc in psutil.process_iter(['name']):
            if is_target_proc(proc, config['sas_process']):
                try:
                    proc.kill()
                    found_active = True
                except: pass

        if not found_active:
            break 
            
        time.sleep(5) 

    # --- PHASE 3: File Deletion ---
    path = os.path.join(config['target_folder'], filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except:
            return False
    return True
