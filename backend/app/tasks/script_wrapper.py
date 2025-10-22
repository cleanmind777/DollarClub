"""
Wrapper to execute user scripts with forced unbuffered output
This ensures all print statements are immediately visible
"""
import sys
import os
import io

# Force completely unbuffered output - use unbuffered binary streams
# then wrap them with TextIOWrapper for proper text handling
sys.stdout = io.TextIOWrapper(
    os.fdopen(sys.stdout.fileno(), 'wb', 0),
    encoding='utf-8',
    write_through=True,  # This is key - bypasses all buffering
    line_buffering=False
)
sys.stderr = io.TextIOWrapper(
    os.fdopen(sys.stderr.fileno(), 'wb', 0),
    encoding='utf-8',
    write_through=True,
    line_buffering=False
)

# Also set environment
os.environ['PYTHONUNBUFFERED'] = '1'

# Patch print function to auto-flush (extra insurance)
original_print = print

def flushed_print(*args, **kwargs):
    """Print with automatic flushing"""
    # Force flush even though write_through should handle it
    kwargs.setdefault('flush', True)
    original_print(*args, **kwargs)
    # Double-flush for absolute certainty
    sys.stdout.flush()

# Replace built-in print with our flushed version
import builtins
builtins.print = flushed_print

# Now execute the user script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: No script file provided")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    if not os.path.exists(script_path):
        print(f"ERROR: Script file not found: {script_path}")
        sys.exit(1)
    
    # Set up the script's directory as the working directory  
    script_dir = os.path.dirname(os.path.abspath(script_path))
    if script_dir:  # Only chdir if there's actually a directory
        os.chdir(script_dir)
    
    # Add script directory to path
    if script_dir:
        sys.path.insert(0, script_dir)
    
    # Execute the script by running it as __main__
    # This is better than exec() for complex scripts
    with open(script_path, 'r', encoding='utf-8') as f:
        script_code = f.read()
    
    # Use compile() then exec() for better error messages
    script_globals = {
        '__name__': '__main__',
        '__file__': script_path,
        '__builtins__': builtins,
    }
    
    try:
        code = compile(script_code, script_path, 'exec')
        exec(code, script_globals)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n[Script interrupted by user]", flush=True)
        sys.exit(130)
    except Exception as e:
        print(f"\n[Script error: {type(e).__name__}: {e}]", flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

