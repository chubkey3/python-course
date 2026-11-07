#!/bin/bash
# Run PrairieLearn locally with this course, with workspaces and external grading enabled.
#
# Run this from a WSL 2 shell (not PowerShell / Git Bash), with Docker Desktop running and
# WSL integration enabled for your distro (Docker Desktop > Settings > Resources > WSL integration):
#
#     bash /mnt/c/Users/jason/python-course/start-local.sh
#
# Then open http://localhost:3000/pl
#
# To match what us.prairielearn.com is running, use:  PL_IMAGE=prairielearn/prairielearn:us-prod-live
set -euo pipefail

COURSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBS_DIR="$HOME/pl_ag_jobs" # must live inside WSL, not on /mnt/c
PL_IMAGE="${PL_IMAGE:-prairielearn/prairielearn}"

mkdir -p "$JOBS_DIR"

echo "Course:   $COURSE_DIR"
echo "Jobs dir: $JOBS_DIR"
echo "Image:    $PL_IMAGE"

docker run -it --rm -p 3000:3000 \
  -v "$COURSE_DIR:/course" \
  -v "$JOBS_DIR:/jobs" \
  -e HOST_JOBS_DIR="$JOBS_DIR" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --add-host=host.docker.internal:172.17.0.1 \
  "$PL_IMAGE"
