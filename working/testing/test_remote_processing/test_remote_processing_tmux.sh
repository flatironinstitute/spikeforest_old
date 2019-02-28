#!/bin/bash
SESSION=mod

tmux -2 new-session -d -s $SESSION

# Y window Y1 pane
tmux new-window -t $SESSION:2 -n 'app'
tmux split-window -h
tmux split-window -h
tmux select-pane -t 0
tmux send-keys "./001_start_test_servers.sh" C-m

# Y window Y2 pane
tmux select-pane -t 1
tmux send-keys "./002_start_compute_resource.sh" C-m

# Y window Y3 pane
tmux select-pane -t 2
tmux send-keys "sleep 2 && ./003_process_toy_example.sh" C-m

tmux new-window -t $SESSION:3 -n 'dev'
tmux select-window -t $SESSION:3

tmux -2 attach-session -t $SESSION