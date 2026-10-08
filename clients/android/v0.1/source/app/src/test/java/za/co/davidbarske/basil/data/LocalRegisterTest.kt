package za.co.davidbarske.basil.data

import java.io.File
import java.nio.file.Files
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState

class LocalRegisterTest {
    private val fixtures = File(System.getProperty("sybil.fixture.dir"))
    private fun legacy(doneCount: Int): ByteArray {
        val root = JSONObject(File(fixtures, "android-v01.json").readText())
        val original = root.getJSONArray("tasks").getJSONObject(0)
        val tasks = JSONArray().put(JSONObject(original.toString()).put("id", "visible"))
        (1..doneCount).forEach {
            tasks.put(JSONObject(original.toString()).put("id", "done-$it")
                .put("state", "DONE").put("completedAt", 1700000001000))
        }
        root.put("tasks", tasks)
        return ("  " + root.toString(2) + "\r\n").toByteArray(Charsets.UTF_8)
    }

    private fun withStore(bytes: ByteArray, block: (JsonTaskRepository, File, File) -> Unit) {
        val directory = Files.createTempDirectory("sybil-local-test").toFile()
        try {
            val file = File(directory, "basil_tasks_v01.json")
            file.writeBytes(bytes)
            block(JsonTaskRepository(directory), file, directory)
        } finally { directory.deleteRecursively() }
    }

    private fun reject(block: () -> Unit) {
        try { block(); fail("Expected unsafe operation to fail") } catch (_: Exception) { }
    }

    @Test fun ordinaryLegacyLocalRegisterLoadsWithoutRewriting() {
        val bytes = File(fixtures, "android-v01.json").readBytes()
        withStore(bytes) { repository, file, _ ->
            val snapshot = repository.readSnapshot()
            assertNull(snapshot.sourceProblem)
            assertEquals(TaskJsonCodec.decode(bytes.decodeToString()), snapshot.tasks)
            assertEquals(snapshot.tasks, repository.loadAll())
            assertArrayEquals(bytes, file.readBytes())
        }
    }

    @Test fun oneHistoricalDoneKeepsValidatedTasksAndExactSourceAvailable() {
        val bytes = legacy(1)
        withStore(bytes) { repository, file, directory ->
            val snapshot = repository.readSnapshot()
            assertEquals(listOf("visible"), snapshot.tasks.map { it.id })
            val source = snapshot.sourceProblem!!
            assertTrue(source.legacyReconciliation)
            assertEquals(listOf("done-1"), source.taskIds)
            assertTrue(source.message.contains("done-1"))
            assertArrayEquals(bytes, source.exportBytes())
            source.exportBytes().fill(0)
            assertArrayEquals(bytes, source.exportBytes())
            reject { repository.loadAll() }
            reject { repository.upsert(snapshot.tasks.single().copy(description = "Changed")) }
            reject { repository.delete("visible") }
            reject { repository.replaceAll(snapshot.tasks) }
            reject { repository.importJson(TaskJsonCodec.encode(listOf(TaskRecord("new", "New", TaskState.ACTIVE)))) }
            reject { repository.reconcileLocal(TaskJsonCodec.encode(snapshot.tasks)) }
            assertArrayEquals(bytes, file.readBytes())
            assertFalse(File(directory, "basil_tasks_v01.legacy-original.json").exists())
        }
    }

    @Test fun multipleHistoricalDoneIdsAreSeparateFromCanonicalTaskState() {
        val bytes = legacy(2)
        withStore(bytes) { repository, file, _ ->
            val snapshot = repository.readSnapshot()
            assertEquals(listOf("done-1", "done-2"), snapshot.sourceProblem!!.taskIds)
            assertEquals(listOf("visible"), snapshot.tasks.map { it.id })
            assertTrue(snapshot.tasks.all { it.state == TaskState.ACTIVE })
            assertArrayEquals(bytes, snapshot.sourceProblem!!.exportBytes())
            assertArrayEquals(bytes, file.readBytes())
        }
    }

    @Test fun malformedOrNonUtf8SourceIsRecoverableButNeverOperational() {
        val sources = listOf("{ invalid JSON".toByteArray(), "{\"unrelated\":true}".toByteArray(),
            byteArrayOf(0xc3.toByte(), 0x28))
        for (bytes in sources) withStore(bytes) { repository, file, _ ->
            val snapshot = repository.readSnapshot()
            assertTrue(snapshot.tasks.isEmpty())
            assertFalse(snapshot.sourceProblem!!.legacyReconciliation)
            assertTrue(snapshot.sourceProblem!!.taskIds.isEmpty())
            assertArrayEquals(bytes, snapshot.sourceProblem!!.exportBytes())
            reject { repository.replaceAll(emptyList()) }
            reject { repository.upsert(TaskRecord("new", "New", TaskState.ACTIVE)) }
            assertArrayEquals(bytes, file.readBytes())
        }
    }

    @Test fun blankLegacyEvidenceRequiresReconciliationWithoutLegitimisingDone() {
        val root = JSONObject(legacy(1).decodeToString())
        for (evidence in listOf(listOf(" "), listOf("proof:synthetic", "\t"))) {
            root.getJSONArray("tasks").getJSONObject(1).put("completionEvidence", JSONArray(evidence))
            val bytes = root.toString().toByteArray()
            withStore(bytes) { repository, file, _ ->
                val snapshot = repository.readSnapshot()
                assertEquals(listOf("done-1"), snapshot.sourceProblem!!.taskIds)
                assertTrue(snapshot.sourceProblem!!.legacyReconciliation)
                assertEquals(listOf("visible"), snapshot.tasks.map { it.id })
                reject { repository.loadAll() }
                assertArrayEquals(bytes, snapshot.sourceProblem!!.exportBytes())
                assertArrayEquals(bytes, file.readBytes())
            }
        }
    }

    @Test fun anExistingDifferentRecoveryBackupIsNeverOverwritten() {
        val bytes = legacy(1)
        withStore(bytes) { repository, file, directory ->
            val backup = File(directory, "basil_tasks_v01.legacy-original.json")
            val earlier = "Earlier retained source".toByteArray()
            backup.writeBytes(earlier)
            val corrected = JSONObject(bytes.decodeToString())
            corrected.getJSONArray("tasks").getJSONObject(1)
                .put("completionEvidence", JSONArray().put("proof:synthetic"))
            reject { repository.reconcileLocal(corrected.toString()) }
            assertArrayEquals(bytes, file.readBytes())
            assertArrayEquals(earlier, backup.readBytes())
        }
    }

    @Test fun canonicalDoneWithoutEvidenceStillFailsRatherThanEnteringLegacyRecovery() {
        val root = JSONObject(File(fixtures, "canonical-v1.json").readText())
        root.getJSONArray("tasks").getJSONObject(0).put("state", "DONE")
        val bytes = root.toString().toByteArray()
        withStore(bytes) { repository, file, _ ->
            assertFalse(repository.readSnapshot().sourceProblem!!.legacyReconciliation)
            reject { repository.loadAll() }
            assertArrayEquals(bytes, file.readBytes())
        }
    }

    @Test fun successfulExplicitRecoveryRetainsOriginalAndAllCanonicalFacts() {
        val bytes = legacy(2)
        withStore(bytes) { repository, _, directory ->
            val corrected = JSONObject(bytes.decodeToString())
            val tasks = corrected.getJSONArray("tasks")
            (1 until tasks.length()).forEach {
                tasks.getJSONObject(it).put("completionEvidence", JSONArray().put("proof:synthetic-$it"))
            }
            // Canonical input can omit client timestamps without losing the original metadata.
            val supplied = TaskJsonCodec.decode(corrected.toString()).map {
                it.copy(project = "", nextAction = "", notes = "", createdAt = null,
                    updatedAt = null, completedAt = null, hasClientMetadata = false)
            }
            repository.reconcileLocal(TaskJsonCodec.encode(supplied))
            assertNull(repository.readSnapshot().sourceProblem)
            assertEquals(setOf("visible", "done-1", "done-2"), repository.loadAll().map { it.id }.toSet())
            assertEquals(2, repository.loadAll().count { it.state == TaskState.DONE })
            assertTrue(repository.loadAll().all { it.project == "Old project" })
            assertArrayEquals(bytes, File(directory, "basil_tasks_v01.legacy-original.json").readBytes())
        }
    }

    @Test fun failedRecoveryCannotChangeOriginalFactsOrReactivateHistoricalDone() {
        val bytes = legacy(1)
        withStore(bytes) { repository, file, directory ->
            val corrected = JSONObject(bytes.decodeToString())
            corrected.getJSONArray("tasks").getJSONObject(1)
                .put("completionEvidence", JSONArray().put("proof:synthetic"))
            val valid = TaskJsonCodec.decode(corrected.toString())
            reject { repository.reconcileLocal(TaskJsonCodec.encode(valid.map { it.copy(description = "Changed") })) }
            reject { repository.reconcileLocal(TaskJsonCodec.encode(valid.map {
                if (it.state == TaskState.DONE) it.copy(state = TaskState.ACTIVE, completionEvidence = emptyList()) else it
            })) }
            assertArrayEquals(bytes, file.readBytes())
            assertFalse(File(directory, "basil_tasks_v01.legacy-original.json").exists())
        }
    }

    @Test fun newIdImportWorksAndIdenticalCanonicalIdRetainsLocalMetadata() {
        val local = TaskRecord("same", "Task", TaskState.ACTIVE, notes = "Local", updatedAt = 100)
        withStore(TaskJsonCodec.encode(listOf(local)).toByteArray()) { repository, _, _ ->
            val sameCanonical = local.copy(notes = "Imported", updatedAt = 999)
            val fresh = TaskRecord("new", "New task", TaskState.WAITING)
            repository.importJson(TaskJsonCodec.encode(listOf(sameCanonical, fresh)))
            assertEquals(listOf(local, fresh), repository.loadAll())
        }
    }

    @Test fun conflictingCanonicalIdsNeverUseKnownUnknownOrEqualTimestampsAsAuthority() {
        val cases = listOf(100L to 200L, 100L to null, null to 200L, 100L to 100L)
        for ((localTime, importedTime) in cases) {
            val local = TaskRecord("same", "Local content", TaskState.ACTIVE, updatedAt = localTime)
            val candidate = local.copy(description = "Conflicting content", updatedAt = importedTime)
            val before = TaskJsonCodec.encode(listOf(local)).toByteArray()
            withStore(before) { repository, file, _ ->
                val input = TaskJsonCodec.encode(listOf(TaskRecord("new", "New", TaskState.ACTIVE), candidate))
                try {
                    repository.importJson(input)
                    fail("Timestamp selected canonical content")
                } catch (error: CanonicalImportConflict) {
                    assertEquals(listOf("same"), error.taskIds)
                    assertEquals(listOf(local), error.localTasks)
                    assertEquals(listOf(candidate), error.incomingTasks)
                    assertEquals(input, error.originalPayload)
                }
                assertEquals(listOf(local), repository.loadAll())
                assertArrayEquals(before, file.readBytes())
            }
        }
    }

    @Test fun localDeletionIsNotACanonicalStateOrHistoryInstruction() {
        val removed = TaskRecord("removed", "Local task", TaskState.DONE, completionEvidence = listOf("proof"))
        val retained = TaskRecord("retained", "Other task", TaskState.ACTIVE)
        val canonicalView = listOf(removed, retained)
        withStore(TaskJsonCodec.encode(canonicalView).toByteArray()) { repository, _, _ ->
            repository.delete("removed")
            assertEquals(listOf(retained), repository.loadAll())
            assertEquals(listOf(removed, retained), canonicalView)
            assertEquals(setOf("ACTIVE", "WAITING", "SCHEDULED", "BLOCKED", "MONITOR", "DONE"),
                TaskState.entries.map { it.name }.toSet())
            val exported = JSONObject(TaskJsonCodec.encode(repository.loadAll()))
            assertFalse(exported.has("deleted_ids"))
            assertFalse(exported.has("tombstones"))
        }
    }
}
