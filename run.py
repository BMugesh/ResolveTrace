import sys, os, subprocess
def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg in ('--eval', '-e', 'eval'):
            print('Running full benchmark evaluation suite...')
            subprocess.run([sys.executable, 'scripts/evaluate.py'])
            return
        elif arg in ('--ui', '-u', 'ui', 'web'):
            print('Launching Streamlit Web Dashboard...')
            subprocess.run(['streamlit', 'run', 'app/ui.py'])
            return
        elif arg in ('--test', '-t', 'test'):
            print('Running all unit tests...')
            subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'])
            return
        else:
            subprocess.run([sys.executable, 'scripts/run_demo.py'] + sys.argv[1:])
            return
    subprocess.run([sys.executable, 'scripts/run_demo.py'])
if __name__ == '__main__':
    main()
