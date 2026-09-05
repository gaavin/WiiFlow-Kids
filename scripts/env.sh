#!/usr/bin/env bash
# Host-side toolchain for WiiFlow Kids.
# The official devkitPPC release is x86_64. On aarch64 we run it under box64
# with the dynarec off: GCC 12's libstdc++ constexpr bits ICE under BOX64_DYNAREC=1.

_wiiflow_find_store_bin() {
	local name="$1" glob="$2"
	if command -v "$name" >/dev/null 2>&1; then
		command -v "$name"
		return 0
	fi
	local found
	found=$(ls -1d /nix/store/*-"$glob"-*/bin/"$name" 2>/dev/null | head -n 1)
	if [ -n "$found" ] && [ -x "$found" ]; then
		printf '%s\n' "$found"
		return 0
	fi
	return 1
}

_wiiflow_find_box64() { _wiiflow_find_store_bin box64 box64; }
_wiiflow_find_make() { _wiiflow_find_store_bin make gnumake; }

_wiiflow_host=$(uname -m)
export DEVKITPRO="${DEVKITPRO:-/tmp/devkitpro/opt/devkitpro}"
export DEVKITPPC="${DEVKITPPC:-$DEVKITPRO/devkitPPC}"

if [ ! -x "$DEVKITPPC/bin/powerpc-eabi-gcc" ]; then
	echo "env.sh: missing powerpc-eabi-gcc in $DEVKITPPC/bin" >&2
	echo "env.sh: unpack devkitPPC r42+ to $DEVKITPRO" >&2
	return 1 2>/dev/null || exit 1
fi

case "$_wiiflow_host" in
	aarch64|arm64)
		_box64=$(_wiiflow_find_box64) || {
			echo "env.sh: aarch64 host needs box64 on PATH (or in /nix/store)" >&2
			return 1 2>/dev/null || exit 1
		}
		export PATH="$(dirname "$_box64"):$PATH"
		# Interpreter mode: dynarec trips a GCC constexpr ICE in libstdc++.
		export BOX64_DYNAREC="${BOX64_DYNAREC:-0}"
		export BOX64_NOBANNER="${BOX64_NOBANNER:-1}"
		export BOX64_LOG="${BOX64_LOG:-0}"
		;;
esac

_make=$(_wiiflow_find_make) || {
	echo "env.sh: GNU make not found (install gnumake or put make on PATH)" >&2
	return 1 2>/dev/null || exit 1
}
export PATH="$(dirname "$_make"):$DEVKITPPC/bin:$DEVKITPRO/tools/bin:$PATH"
unset _wiiflow_host _box64 _make
