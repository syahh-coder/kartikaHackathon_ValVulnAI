#!/bin/sh
set -eu
# Runs only as a container bootstrap, then drops every capability and root UID.
# Immutable destinations match boundary/contracts.py and Compose IPAM.
iptables -w -F
iptables -w -P INPUT DROP
iptables -w -P OUTPUT DROP
iptables -w -P FORWARD DROP
iptables -w -A INPUT -i lo -j ACCEPT
iptables -w -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -w -A OUTPUT -d 127.0.0.11 -j REJECT
iptables -w -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
if [ "$1" = worker ]; then
    iptables -w -A OUTPUT -d 172.30.74.3 -p tcp --dport 8001 -m conntrack --ctstate NEW -j ACCEPT
elif [ "$1" = lab ]; then
    iptables -w -A INPUT -s 172.30.74.2 -p tcp --dport 8001 -j ACCEPT
    if [ "${LAB_SHARED_MANUAL:-0}" = "1" ]; then
        [ "${LAB_MANUAL_ORIGIN:-}" = "http://127.0.0.1:8001" ] || exit 1
        # Compose binds this port to host loopback. Egress/forwarding stay denied.
        iptables -w -A INPUT -p tcp --dport 8001 -j ACCEPT
    fi
    iptables -w -A OUTPUT -o lo -j ACCEPT
elif [ "$1" = manual ]; then
    # Separate manual-only bridge: Docker publishes this port on host loopback.
    # New outbound connections remain blocked; the service then loses all caps.
    case "${LAB_MANUAL_ORIGIN:-}" in
        http://127.0.0.1:8001|http://127.0.0.1:8002) ;;
        *) exit 1 ;;
    esac
    iptables -w -A INPUT -p tcp --dport 8001 -j ACCEPT
    iptables -w -A OUTPUT -o lo -j ACCEPT
else
    exit 1
fi
iptables -w -A OUTPUT -j REJECT
ip6tables -w -F
ip6tables -w -P INPUT DROP
ip6tables -w -P OUTPUT DROP
ip6tables -w -P FORWARD DROP
shift
exec setpriv --reuid=10001 --regid=10001 --clear-groups --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs "$@"
