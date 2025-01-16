for i in {1..5}; do
    (
        echo "Iteration $i:"
        deepaas-run --listen-ip 0.0.0.0 --listen-port $((5000 + i)) &
        sleep 10
        python3 ./UI/launch.py --api_url http://0.0.0.0:$((5000 + i))/ --ui_port $((80 + i))
    ) &
done
wait