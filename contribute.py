#!/usr/bin/env python
import argparse
import os
import random
import shutil
import stat
from datetime import datetime
from datetime import timedelta
from subprocess import Popen
import sys

HOURLY_WEIGHTS = {
    0: 2, 1: 1, 2: 0, 3: 0, 4: 0, 5: 1, 6: 3, 7: 8,
    8: 25, 9: 75, 10: 95, 11: 85, 12: 30, 13: 60,
    14: 90, 15: 85, 16: 70, 17: 50, 18: 35, 19: 30,
    20: 25, 21: 15, 22: 10, 23: 5
}

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv',
    'dist', 'build', '.idea', '.vscode', '.next', 'out'
}

IGNORE_FILES = {
    '.DS_Store', 'thumbs.db', '.env', '.env.local'
}

MOCK_FILES = {
    'src/auth.py': [
        "def authenticate_user(username, password_hash):",
        "    # Query database for user credentials",
        "    user = db.query('SELECT * FROM users WHERE username = ?', (username,))",
        "    if not user:",
        "        return False",
        "    return verify_hash(password_hash, user['password_hash'])",
        "",
        "def get_user_session(session_id):",
        "    return redis.get(f'session:{session_id}')"
    ],
    'src/utils.py': [
        "import hashlib",
        "import time",
        "",
        "def verify_hash(raw, hashed):",
        "    return hashlib.sha256(raw.encode()).hexdigest() == hashed",
        "",
        "def get_unix_timestamp():",
        "    return int(time.time())"
    ],
    'src/db.py': [
        "import sqlite3",
        "",
        "class DatabaseConnection:",
        "    def __init__(self, db_path='app.db'):",
        "        self.db_path = db_path",
        "",
        "    def query(self, sql, params=()):",
        "        with sqlite3.connect(self.db_path) as conn:",
        "            conn.row_factory = sqlite3.Row",
        "            cursor = conn.cursor()",
        "            cursor.execute(sql, params)",
        "            return cursor.fetchone()"
    ],
    'tests/test_app.py': [
        "import unittest",
        "from src.utils import verify_hash",
        "",
        "class TestAppUtils(unittest.TestCase):",
        "    def test_hash_verification(self):",
        "        raw_text = 'secret_password'",
        "        hashed = '7ef4094a9a084c8a29a008c2a939023efd77977464ea9f470559eb4cfb63897b'",
        "        self.assertTrue(verify_hash(raw_text, hashed))"
    ],
    'config/settings.json': [
        "{\n  \"app_name\": \"CoreService\",\n  \"version\": \"1.4.2\",\n  \"port\": 8080,\n  \"db_driver\": \"sqlite3\",\n  \"rate_limit\": 100\n}"
    ],
    'README.md': [
        "# CoreService",
        "",
        "A simulated service to manage user identities and core utilities.",
        "",
        "## Getting Started",
        "1. Run tests with `python -m unittest discover tests`",
        "2. Configure application settings in `config/settings.json`"
    ]
}


def remove_readonly(func, path, exc_info):
    """Helper to clear read-only permissions on Windows file deletion errors."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def clean_repositories(target_repo_name=None):
    """Removes all locally generated 'repository-*' directories and target repo directory."""
    cwd = os.getcwd()
    removed_count = 0

    for item in os.listdir(cwd):
        item_path = os.path.join(cwd, item)
        if os.path.isdir(item_path):
            if item.startswith('repository-') or (target_repo_name and item == target_repo_name):
                print(f"Cleaning repository directory: {item}...")
                try:
                    shutil.rmtree(item_path, onerror=remove_readonly)
                    removed_count += 1
                except Exception as e:
                    print(f"Failed to delete {item}: {e}")

    print(f"\nCleanup complete. Removed {removed_count} generated repository directory/directories.")


def scan_project(project_dir):
    """Scans local project directory and returns dict of relative paths to line lists."""
    project_files = {}
    project_dir = os.path.abspath(project_dir)
    
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('repository-')]
        
        for file in files:
            if file in IGNORE_FILES or file.endswith('.pyc'):
                continue
            
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, project_dir).replace('\\', '/')
            
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.rstrip('\r\n') for line in f]
                project_files[rel_path] = lines
            except Exception as e:
                print(f"Skipping binary/unreadable file: {rel_path} ({e})")
                
    return project_files


def prepare_project_chunks(project_files, target_total_chunks=100):
    """Breaks project files into dynamically sized chunks calibrated to total date range slots."""
    chunks = []
    
    total_lines = sum(len(lines) for lines in project_files.values())
    if target_total_chunks > 0 and total_lines > 0:
        lines_per_chunk = max(10, min(50, total_lines // max(1, target_total_chunks)))
    else:
        lines_per_chunk = 15

    def file_priority(rel_path):
        lower = rel_path.lower()
        if 'readme' in lower or 'license' in lower:
            return 0
        if 'package.json' in lower or 'settings' in lower or 'config' in lower or 'requirements' in lower:
            return 1
        if lower.startswith('src') or lower.startswith('lib'):
            return 2
        if 'test' in lower:
            return 4
        return 3

    sorted_paths = sorted(project_files.keys(), key=file_priority)

    for rel_path in sorted_paths:
        lines = project_files[rel_path]
        if not lines:
            chunks.append({
                'rel_path': rel_path,
                'action': 'init',
                'lines': []
            })
            continue
        
        start_idx = 0
        chunk_num = 0
        while start_idx < len(lines):
            chunk_size = random.randint(max(5, lines_per_chunk - 5), lines_per_chunk + 10)
            end_idx = min(len(lines), start_idx + chunk_size)
            chunk_lines = lines[start_idx:end_idx]
            
            chunks.append({
                'rel_path': rel_path,
                'action': 'init' if chunk_num == 0 else 'append',
                'lines': chunk_lines
            })
            start_idx = end_idx
            chunk_num += 1
            
    return chunks


def extract_scope(file_path):
    """Derives realistic commit scope from file directory/name."""
    filename = os.path.basename(file_path)
    lower = file_path.lower()
    
    if 'readme' in lower:
        return 'docs'
    if 'test' in lower:
        return 'test'
    if 'config' in lower or 'setting' in lower or 'package.json' in lower:
        return 'config'
    if 'auth' in lower or 'login' in lower or 'user' in lower:
        return 'auth'
    if 'db' in lower or 'database' in lower or 'model' in lower or 'sql' in lower:
        return 'db'
    if 'api' in lower or 'route' in lower or 'controller' in lower or 'server' in lower:
        return 'api'
    if 'util' in lower or 'helper' in lower:
        return 'utils'
    if 'ui' in lower or 'view' in lower or 'component' in lower or 'css' in lower or 'style' in lower:
        return 'ui'
    
    parent = os.path.basename(os.path.dirname(file_path))
    if parent and parent not in ['.', 'src', 'lib']:
        return parent.lower()
    return os.path.splitext(filename)[0].lower()


def generate_commit_message(file_path, action):
    """Generates realistic scoped conventional commit messages."""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    scope = extract_scope(file_path)

    if action == 'init':
        if ext in ['.md', '.txt', '.rst']:
            return f"docs({scope}): initialize {filename} project overview"
        elif ext in ['.py', '.java', '.go', '.rs', '.cpp', '.c']:
            return f"feat({scope}): create {filename} core module"
        elif ext in ['.js', '.ts', '.jsx', '.tsx', '.vue']:
            return f"feat({scope}): add baseline {filename} component"
        elif ext in ['.json', '.yaml', '.yml', '.toml', '.env', '.config']:
            return f"chore({scope}): add initial {filename} configuration"
        elif ext in ['.css', '.scss', '.html']:
            return f"style({scope}): add baseline {filename} layout"
        return f"feat({scope}): create {filename}"
    else:
        if ext in ['.md', '.txt', '.rst']:
            msg_options = [
                f"docs({scope}): update setup and usage instructions in {filename}",
                f"docs({scope}): expand documentation and API details in {filename}",
                f"docs({scope}): refine formatting and section notes in {filename}"
            ]
        elif ext in ['.py', '.java', '.go', '.rs', '.cpp', '.c']:
            if 'test' in scope:
                msg_options = [
                    f"test({scope}): add test assertions in {filename}",
                    f"test({scope}): expand test coverage for {filename}",
                    f"test({scope}): mock service dependencies in {filename}"
                ]
            else:
                msg_options = [
                    f"feat({scope}): implement core handler logic in {filename}",
                    f"refactor({scope}): optimize function execution in {filename}",
                    f"fix({scope}): handle edge case validation in {filename}",
                    f"refactor({scope}): clean up internal data processing in {filename}",
                    f"perf({scope}): optimize data retrieval flow in {filename}"
                ]
        elif ext in ['.js', '.ts', '.jsx', '.tsx', '.vue']:
            msg_options = [
                f"feat({scope}): implement component state and handlers in {filename}",
                f"refactor({scope}): extract helper logic into {filename}",
                f"fix({scope}): resolve props rendering issue in {filename}",
                f"perf({scope}): optimize render cycle in {filename}"
            ]
        elif ext in ['.json', '.yaml', '.yml', '.toml', '.config']:
            msg_options = [
                f"config({scope}): update environment parameters in {filename}",
                f"chore({scope}): bump dependencies and version in {filename}",
                f"config({scope}): adjust runtime settings in {filename}"
            ]
        elif ext in ['.css', '.scss', '.html']:
            msg_options = [
                f"style({scope}): update layout and responsive rules in {filename}",
                f"style({scope}): refine component styling and theme in {filename}"
            ]
        else:
            msg_options = [
                f"refactor({scope}): update {filename} implementation",
                f"fix({scope}): patch functionality in {filename}"
            ]
        return random.choice(msg_options)


def generate_daily_commit_times(day, count):
    """Generates realistic intra-day commit times separated by 25-75 min coding sessions."""
    hours = list(HOURLY_WEIGHTS.keys())
    weights = list(HOURLY_WEIGHTS.values())
    
    start_hour = random.choices(hours, weights=weights, k=1)[0]
    start_minute = random.randint(5, 55)
    current_time = day.replace(hour=start_hour, minute=start_minute, second=random.randint(0, 59))
    
    times = [current_time]
    for _ in range(count - 1):
        gap = timedelta(minutes=random.randint(25, 75))
        current_time += gap
        
        if current_time.hour == 12 and current_time.minute > 30:
            current_time += timedelta(minutes=random.randint(45, 75))
        if current_time.hour >= 23:
            current_time = current_time.replace(hour=22, minute=random.randint(0, 59))
            
        times.append(current_time)
        
    return times


def main(def_args=sys.argv[1:]):
    args = arguments(def_args)
    
    target_repo_name = None
    if args.repository:
        start = args.repository.rfind('/') + 1
        end = args.repository.rfind('.')
        target_repo_name = args.repository[start:end]

    if args.clean:
        clean_repositories(target_repo_name)
        sys.exit(0)

    curr_date = datetime.now()
    directory = 'repository-' + curr_date.strftime('%Y-%m-%d-%H-%M-%S')
    repository = args.repository
    user_name = args.user_name
    user_email = args.user_email

    if repository is not None:
        directory = target_repo_name

    no_weekends = args.no_weekends
    frequency = args.frequency

    start_date, total_days = calculate_date_range(args, curr_date)

    project_files = None
    project_chunks = []
    chunk_index = 0

    if args.project_dir:
        if not os.path.exists(args.project_dir):
            sys.exit(f"Error: Specified project directory '{args.project_dir}' does not exist.")
        print(f"Scanning project directory: {args.project_dir}...")
        project_files = scan_project(args.project_dir)
        if not project_files:
            sys.exit("Error: No readable files found in the specified project directory.")
        print(f"Discovered {len(project_files)} project files.")

        estimated_active_days = max(1, int(total_days * (frequency / 100.0)))
        max_daily_commits = min(args.max_commits, 15)
        target_chunks = estimated_active_days * max_daily_commits
        
        project_chunks = prepare_project_chunks(project_files, target_total_chunks=target_chunks)

    if not os.path.exists(directory):
        os.mkdir(directory)
    os.chdir(directory)
    run(['git', 'init', '-b', 'main'])

    if user_name is not None:
        run(['git', 'config', 'user.name', user_name])

    if user_email is not None:
        run(['git', 'config', 'user.email', user_email])

    vacation_days_left = 0

    for day_offset in range(total_days):
        day = start_date + timedelta(days=day_offset)

        if vacation_days_left > 0:
            vacation_days_left -= 1
            continue

        if random.randint(0, 100) < 2:
            vacation_days_left = random.randint(4, 12)
            continue

        is_weekend = day.weekday() >= 5
        if no_weekends and is_weekend:
            continue

        if is_weekend:
            is_active_day = random.randint(0, 100) < 10
        else:
            is_active_day = random.randint(0, 100) < frequency

        if is_active_day:
            commits_today = contributions_per_day(args)
            commit_times = generate_daily_commit_times(day, commits_today)

            for commit_time in commit_times:
                chunk_index = execute_commit(commit_time, project_chunks, chunk_index, project_files)

    curr_day_offset = total_days - 1
    while project_chunks and chunk_index < len(project_chunks):
        day = start_date + timedelta(days=curr_day_offset)
        remaining = len(project_chunks) - chunk_index
        commits_today = min(15, remaining, random.randint(3, 10))
        commit_times = generate_daily_commit_times(day, commits_today)
        
        for commit_time in commit_times:
            if chunk_index < len(project_chunks):
                chunk_index = execute_commit(commit_time, project_chunks, chunk_index, project_files)
        curr_day_offset += 1

    if repository is not None:
        run(['git', 'remote', 'add', 'origin', repository])
        run(['git', 'branch', '-M', 'main'])
        run(['git', 'push', '-f', '-u', 'origin', 'main'])

    print('\nRepository generation ' +
          '\x1b[6;30;42mcompleted successfully\x1b[0m!')


def execute_commit(commit_time, project_chunks, chunk_index, project_files):
    """Executes a single commit using project chunks or mock files fallback."""
    if project_chunks:
        if chunk_index < len(project_chunks):
            chunk = project_chunks[chunk_index]
            chunk_index += 1
            file_path = chunk['rel_path']
            action = chunk['action']
            lines = chunk['lines']

            dirname = os.path.dirname(file_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

            if action == 'init' or not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                    if lines:
                        f.write("\n".join(lines) + "\n")
                commit_msg = generate_commit_message(file_path, 'init')
            else:
                with open(file_path, 'a', encoding='utf-8', errors='ignore') as f:
                    if lines:
                        f.write("\n" + "\n".join(lines) + "\n")
                    else:
                        f.write(f"\n# Refactor update - {commit_time.strftime('%Y-%m-%d %H:%M')}\n")
                commit_msg = generate_commit_message(file_path, 'append')
        else:
            file_path = random.choice(list(project_files.keys()))
            with open(file_path, 'a', encoding='utf-8', errors='ignore') as f:
                f.write(f"\n# Code optimization - {commit_time.strftime('%Y-%m-%d %H:%M')}\n")
            commit_msg = generate_commit_message(file_path, 'append')
    else:
        file_path = random.choice(list(MOCK_FILES.keys()))
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write("\n".join(MOCK_FILES[file_path]) + "\n")
            commit_msg = generate_commit_message(file_path, 'init')
        else:
            with open(file_path, 'a', encoding='utf-8', errors='ignore') as f:
                f.write(f"\n# Revision patch {random.randint(100, 999)} - verified {commit_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            commit_msg = generate_commit_message(file_path, 'append')

    # Backdate both Author Date and Committer Date
    formatted_date = commit_time.strftime('%Y-%m-%d %H:%M:%S')
    env = os.environ.copy()
    env['GIT_AUTHOR_DATE'] = formatted_date
    env['GIT_COMMITTER_DATE'] = formatted_date

    run(['git', 'add', file_path])
    run(['git', 'commit', '-m', commit_msg, '--date', formatted_date], env=env)

    return chunk_index


def calculate_date_range(args, curr_date):
    """Calculates start_date datetime and total_days count based on args."""
    if args.start_date and args.end_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            sys.exit("Error: Dates must be in YYYY-MM-DD format (e.g. 2025-01-15).")
        if start_date > end_date:
            sys.exit("Error: start_date cannot be after end_date.")
        total_days = (end_date - start_date).days + 1
    elif args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            sys.exit("Error: start_date must be in YYYY-MM-DD format.")
        total_days = args.days_before + args.days_after
    else:
        if args.days_before < 0:
            sys.exit('days_before must not be negative')
        if args.days_after < 0:
            sys.exit('days_after must not be negative')
        start_date = curr_date.replace(hour=0, minute=0, second=0) - timedelta(days=args.days_before)
        total_days = args.days_before + args.days_after

    return start_date, total_days


def run(commands, env=None):
    Popen(commands, env=env).wait()


def contributions_per_day(args):
    max_c = args.max_commits
    if max_c > 15:
        max_c = 15
    if max_c < 1:
        max_c = 1
    return random.randint(1, max_c)


def arguments(argsval):
    parser = argparse.ArgumentParser(description="GitHub Contribution & Project Break-down Commit Simulator")
    parser.add_argument('-c', '--clean', action='store_true', default=False, required=False,
                        help="""Clean up locally generated repository directories.""")
    parser.add_argument('-p', '--project_dir', type=str, required=False,
                        help="""Path to a local project directory. If specified,
                        the script scans your project files and incrementally
                        commits them piece-by-piece over the date range.""")
    parser.add_argument('-sd', '--start_date', type=str, required=False,
                        help="""Start date for commits in YYYY-MM-DD format (e.g. 2025-01-01).""")
    parser.add_argument('-ed', '--end_date', type=str, required=False,
                        help="""End date for commits in YYYY-MM-DD format (e.g. 2026-07-15).""")
    parser.add_argument('-nw', '--no_weekends', action='store_true', default=False,
                        required=False, help="""Do not commit on weekends.""")
    parser.add_argument('-mc', '--max_commits', type=int, default=10,
                        required=False, help="""Maximum commits per day (1 to 15). Default is 10.""")
    parser.add_argument('-fr', '--frequency', type=int, default=60,
                        required=False, help="""Percentage of active days (0-100). Default is 60.""")
    parser.add_argument('-r', '--repository', type=str, required=False,
                        help="""Link to a remote Git repository to push commits.""")
    parser.add_argument('-un', '--user_name', type=str, required=False,
                        help="""Overrides git user.name config.""")
    parser.add_argument('-ue', '--user_email', type=str, required=False,
                        help="""Overrides git user.email config.""")
    parser.add_argument('-db', '--days_before', type=int, default=365,
                        required=False, help="""Number of days before current date. Default is 365.""")
    parser.add_argument('-da', '--days_after', type=int, default=0,
                        required=False, help="""Number of days after current date. Default is 0.""")
    return parser.parse_args(argsval)


if __name__ == "__main__":
    main()