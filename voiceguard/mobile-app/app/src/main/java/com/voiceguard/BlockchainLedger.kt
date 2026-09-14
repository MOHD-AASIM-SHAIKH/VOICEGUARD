package com.voiceguard

import java.security.MessageDigest

data class BlockchainIncident(
    val id: String,
    val timestamp: String,
    val callType: String,
    val app: String,
    val confidence: Float,
    val sha256Hash: String,
    val txHash: String,
    val blockNumber: Long,
    val status: String = "VERIFIED ON-CHAIN"
)

object BlockchainLedger {

    // Smart contract references matching blockchain/contracts/
    const val EVIDENCE_LOG_CONTRACT = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    const val TRANSACTION_AUTHORIZER_CONTRACT = "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
    const val NETWORK_NAME = "Polygon Amoy Testnet"
    const val CHAKSHU_BASE_URL = "https://sancharsaathi.gov.in/sfc/"

    /**
     * Computes canonical SHA-256 evidence hash matching reporting/evidence-hash/hash.py
     */
    fun computeEvidenceHash(incidentId: String, timestamp: String, app: String, confidence: Float): String {
        val canonical = """{"app":"$app","confidenceAtAlert":$confidence,"detectedAt":"$timestamp","incidentId":"$incidentId"}"""
        val digest = MessageDigest.getInstance("SHA-256")
        val hashBytes = digest.digest(canonical.toByteArray(Charsets.UTF_8))
        return hashBytes.joinToString("") { "%02x".format(it) }
    }

    /**
     * Generates deep-link URL for Chakshu fraud reporting matching reporting/chakshu-link-builder/link.py
     */
    fun buildChakshuLink(timestamp: String, callType: String, confidence: Float): String {
        return "$CHAKSHU_BASE_URL?reportedAt=$timestamp&callType=$callType&confidence=$confidence"
    }

    /**
     * Default ledger records initialized with deterministic hashes
     */
    fun createSampleIncidents(): MutableList<BlockchainIncident> {
        val hash1 = computeEvidenceHash("VG-2026-001", "13:42, Today", "WhatsApp", 0.94f)
        val hash2 = computeEvidenceHash("VG-2026-002", "Yesterday, 17:15", "Cellular Call", 0.96f)
        val hash3 = computeEvidenceHash("VG-2026-003", "Sept 10, 09:30", "WhatsApp", 0.91f)

        return mutableListOf(
            BlockchainIncident(
                id = "VG-2026-001",
                timestamp = "13:42 · WhatsApp",
                callType = "voip",
                app = "WhatsApp",
                confidence = 0.94f,
                sha256Hash = "0x${hash1.take(16)}...${hash1.takeLast(8)}",
                txHash = "0x3f8a12bc94e751a02d8f92c10b2849e7a83d4c51",
                blockNumber = 4829104L
            ),
            BlockchainIncident(
                id = "VG-2026-002",
                timestamp = "Yesterday · Call",
                callType = "cellular",
                app = "Phone",
                confidence = 0.96f,
                sha256Hash = "0x${hash2.take(16)}...${hash2.takeLast(8)}",
                txHash = "0x91d4e7a83d4c510b2849e73f8a12bc94e751a02d",
                blockNumber = 4827552L
            ),
            BlockchainIncident(
                id = "VG-2026-003",
                timestamp = "Sept 10 · WhatsApp",
                callType = "voip",
                app = "WhatsApp",
                confidence = 0.91f,
                sha256Hash = "0x${hash3.take(16)}...${hash3.takeLast(8)}",
                txHash = "0x51a02d8f92c10b2849e7a83d4c3f8a12bc94e751",
                blockNumber = 4819302L
            )
        )
    }
}
