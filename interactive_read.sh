#!/bin/bash

file="execution.log"  # Replace with your actual filename
start_line_number=900  # Replace with the line number from which you want to start reading


count=0
while IFS= read -r line; do
    ((count++))
    if (( count >= start_line_number )); then
        read -r -s -p "Press Enter to display the next line..."
        echo "$line"
    fi
done < <(tail -n +$start_line_number "$file")
