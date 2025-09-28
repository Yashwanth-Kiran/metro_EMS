import os

# Try to import pysnmp in a way that works with both 4.x (hlapi) and 7.x (hlapi.v3arch)
IMPORT_STYLE = None
try:
    from pysnmp.hlapi.v3arch import (
        SnmpEngine,
        CommunityData,
        UdpTransportTarget,
        ContextData,
        ObjectType,
        ObjectIdentity,
        getCmd,
        UsmUserData,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmNoAuthProtocol,
        usmDESPrivProtocol,
        usmAesCfb128Protocol,
        usmNoPrivProtocol,
    )
    IMPORT_STYLE = "v3arch"
except Exception:
    try:
        from pysnmp.hlapi import (
            SnmpEngine,
            CommunityData,
            UdpTransportTarget,
            ContextData,
            ObjectType,
            ObjectIdentity,
            getCmd,
            UsmUserData,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmNoAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
            usmNoPrivProtocol,
        )
        IMPORT_STYLE = "hlapi"
    except Exception:
        IMPORT_STYLE = None

if IMPORT_STYLE:
    def _parse_timeout_env(var_name: str, default: float) -> float:
        try:
            val = float(os.getenv(var_name, str(default)))
            return max(0.1, min(val, 10.0))
        except Exception:
            return default

    def _parse_retries_env(var_name: str, default: int) -> int:
        try:
            val = int(os.getenv(var_name, str(default)))
            return max(0, min(val, 5))
        except Exception:
            return default

    def snmp_get(ip, community, oid, *, timeout: float | None = None, retries: int | None = None, version: str | None = None, port: int | None = None):
        """Perform an SNMP GET for the given OID.
        - Uses SNMP v2c by default, falls back to v1 if v2c fails.
        - Timeout and retries can be configured via env:
          METRO_SNMP_TIMEOUT (seconds, default 2.0), METRO_SNMP_RETRIES (default 1)
        - Force version by passing version='2c' or '1'.
        Returns the string value on success, or None on failure.
        """
        try:
            eff_timeout = timeout if timeout is not None else _parse_timeout_env("METRO_SNMP_TIMEOUT", 2.0)
            eff_retries = retries if retries is not None else _parse_retries_env("METRO_SNMP_RETRIES", 1)
            eff_port = int(port or os.getenv("METRO_SNMP_PORT", "161"))

            versions = []
            forced = (version or os.getenv("METRO_SNMP_VERSION", "")).strip()
            if forced in ("2c", "2", "v2c"):
                versions = ["2c"]
            elif forced in ("1", "v1"):
                versions = ["1"]
            else:
                versions = ["2c", "1"]  # try v2c first then v1

            for ver in versions:
                mp_model = 1 if ver == "2c" else 0
                iterator = getCmd(
                    SnmpEngine(),
                    CommunityData(community, mpModel=mp_model),
                    UdpTransportTarget((ip, eff_port), timeout=eff_timeout, retries=eff_retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
                errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
                if errorIndication or errorStatus:
                    # Try next version if available
                    continue
                return str(varBinds[0][1])

            return None
        except Exception:
            return None

    def _map_auth_proto(name: str):
        n = (name or '').strip().upper()
        if n == 'MD5':
            return usmHMACMD5AuthProtocol
        if n == 'SHA' or n == 'SHA1':
            return usmHMACSHAAuthProtocol
        return usmNoAuthProtocol

    def _map_priv_proto(name: str):
        n = (name or '').strip().upper()
        if n == 'DES':
            return usmDESPrivProtocol
        if n == 'AES' or n == 'AES128' or n == 'AES-128':
            return usmAesCfb128Protocol
        return usmNoPrivProtocol

    def snmp_get_v3(ip: str, oid: str, *, username: str, auth_key: str | None = None, priv_key: str | None = None,
                    auth_protocol: str | None = None, priv_protocol: str | None = None,
                    timeout: float | None = None, retries: int | None = None, port: int | None = None):
        try:
            eff_timeout = timeout if timeout is not None else _parse_timeout_env("METRO_SNMP_TIMEOUT", 2.0)
            eff_retries = retries if retries is not None else _parse_retries_env("METRO_SNMP_RETRIES", 1)
            eff_port = int(port or os.getenv("METRO_SNMP_PORT", "161"))

            user = UsmUserData(
                userName=username,
                authKey=auth_key,
                privKey=priv_key,
                authProtocol=_map_auth_proto(auth_protocol or ''),
                privProtocol=_map_priv_proto(priv_protocol or ''),
            )

            iterator = getCmd(
                SnmpEngine(),
                user,
                UdpTransportTarget((ip, eff_port), timeout=eff_timeout, retries=eff_retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            if errorIndication or errorStatus:
                return None
            return str(varBinds[0][1])
        except Exception:
            return None
else:
    # pysnmp not importable; provide safe fallbacks returning None
    import random, socket, struct, time as _time

    def _encode_length(length: int) -> bytes:
        if length < 0x80:
            return bytes([length])
        out = []
        while length > 0:
            out.append(length & 0xFF)
            length >>= 8
        out_bytes = bytes(reversed(out))
        return bytes([0x80 | len(out_bytes)]) + out_bytes

    def _encode_integer(value: int) -> bytes:
        if value == 0:
            content = b"\x00"
        else:
            neg = value < 0
            v = -value if neg else value
            content = b""
            while v:
                content = bytes([v & 0xFF]) + content
                v >>= 8
            if neg:
                # Two's complement for negative numbers not really needed here (request-id >=0)
                pass
            # Ensure top bit not interpreted as sign
            if content[0] & 0x80:
                content = b"\x00" + content
        return b"\x02" + _encode_length(len(content)) + content

    def _encode_octet_string(data: bytes) -> bytes:
        return b"\x04" + _encode_length(len(data)) + data

    def _encode_null() -> bytes:
        return b"\x05\x00"

    def _encode_oid(oid: str) -> bytes:
        # OID like 1.3.6.1.2.1.1.1.0
        parts = [int(x) for x in oid.strip().split('.') if x]
        if len(parts) < 2:
            return b"\x06\x01\x00"
        first_byte = 40 * parts[0] + parts[1]
        encoded = [first_byte]
        for p in parts[2:]:
            if p < 128:
                encoded.append(p)
            else:
                stack = []
                while p > 0:
                    stack.append(0x80 | (p & 0x7F))
                    p >>= 7
                stack[0] &= 0x7F  # clear msb of last byte
                for b in reversed(stack):
                    encoded.append(b)
        content = bytes(encoded)
        return b"\x06" + _encode_length(len(content)) + content

    def _wrap_sequence(content: bytes) -> bytes:
        return b"\x30" + _encode_length(len(content)) + content

    def _build_get_request(community: str, oid: str, request_id: int) -> bytes:
        version = _encode_integer(1)  # SNMP v2c (1); use 0 for v1
        comm = _encode_octet_string(community.encode())
        # variable binding: sequence of (OID, Null)
        vb = _wrap_sequence(_encode_oid(oid) + _encode_null())
        vbl = _wrap_sequence(vb)
        pdu_body = _encode_integer(request_id) + _encode_integer(0) + _encode_integer(0) + vbl
        pdu = bytes([0xA0]) + _encode_length(len(pdu_body)) + pdu_body  # GetRequest-PDU
        return _wrap_sequence(version + comm + pdu)

    def _parse_response(data: bytes, encoded_oid: bytes) -> str | None:
        """Very small BER slice parser: locate requested OID TLV, then read following value TLV."""
        try:
            pos = data.find(encoded_oid)
            if pos == -1:
                return None
            value_pos = pos + len(encoded_oid)
            if value_pos + 2 > len(data):
                return None
            tag = data[value_pos]
            length_byte = data[value_pos + 1]
            idx = value_pos + 2
            if length_byte & 0x80:
                ln_len = length_byte & 0x7F
                if value_pos + 2 + ln_len > len(data):
                    return None
                length = 0
                for b in data[value_pos+2:value_pos+2+ln_len]:
                    length = (length << 8) | b
                idx = value_pos + 2 + ln_len
            else:
                length = length_byte
            value_bytes = data[idx:idx+length]
            if tag == 0x04:  # Octet String
                try:
                    return value_bytes.decode(errors='ignore').strip('\x00') or None
                except Exception:
                    return None
            if tag == 0x02 and length <= 4:  # Integer
                val = 0
                for b in value_bytes:
                    val = (val << 8) | b
                return str(val)
            if tag == 0x43:  # TimeTicks (treat as integer)
                val = 0
                for b in value_bytes:
                    val = (val << 8) | b
                return str(val)
            if tag == 0x06:  # OID
                # Very naive OID decoder
                if not value_bytes:
                    return None
                first = value_bytes[0]
                oid_parts = [str(first // 40), str(first % 40)]
                sub = 0
                for b in value_bytes[1:]:
                    sub = (sub << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        oid_parts.append(str(sub))
                        sub = 0
                return '.'.join(oid_parts)
            # Other tags ignored
            return None
        except Exception:
            return None

    def snmp_get(ip, community, oid, *, timeout: float | None = None, retries: int | None = None, version: str | None = None, port: int | None = None):
        # Raw UDP fallback (SNMP v2c assumed). Only GET support.
        retries = retries if retries is not None else 1
        timeout = timeout if timeout is not None else 2.0
        port = port or int(os.getenv("METRO_SNMP_PORT", "161"))
        request_id = random.randint(1, 0x7FFFFFFF)
        packet = _build_get_request(community, oid, request_id)
        encoded_oid = _encode_oid(oid)
        for _ in range(retries + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(timeout)
                    s.sendto(packet, (ip, port))
                    data, _addr = s.recvfrom(4096)
                    val = _parse_response(data, encoded_oid)
                    if val:
                        return val
            except Exception:
                _time.sleep(0.05)
        return None

    def snmp_get_v3(ip: str, oid: str, *, username: str, auth_key: str | None = None, priv_key: str | None = None,
                    auth_protocol: str | None = None, priv_protocol: str | None = None,
                    timeout: float | None = None, retries: int | None = None, port: int | None = None):
        # Not supported in fallback
        return None
