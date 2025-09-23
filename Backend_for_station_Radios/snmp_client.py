try:
    from pysnmp.hlapi import *
    def snmp_get(ip, community, oid):
        try:
            iterator = getCmd(SnmpEngine(),
                              CommunityData(community, mpModel=1),
                              UdpTransportTarget((ip, 161), timeout=0.5, retries=0),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)))
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            if errorIndication or errorStatus:
                return None
            return str(varBinds[0][1])
        except Exception:
            return None
except ImportError:
    def snmp_get(ip, community, oid):
        # Fallback for Windows/systems without SNMP
        print(f"SNMP query simulated: {ip} {community} {oid}")
        return "Simulated SNMP Response"
