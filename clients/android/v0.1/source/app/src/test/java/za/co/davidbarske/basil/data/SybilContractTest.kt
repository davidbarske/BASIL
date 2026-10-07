package za.co.davidbarske.basil.data

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState

class SybilContractTest {
    private val fixtures = File(System.getProperty("sybil.fixture.dir"))
    private val proof = File(System.getProperty("sybil.proof.dir"))
    private fun reject(block: () -> Unit) {
        try { block(); fail("Invalid contract was accepted") } catch (_: Exception) { }
    }
    private fun sameJson(expected: Any?, actual: Any?) {
        when (expected) {
            is JSONObject -> {
                assertTrue(actual is JSONObject)
                actual as JSONObject
                val keys = expected.keys().asSequence().toSet()
                assertEquals(keys, actual.keys().asSequence().toSet())
                keys.forEach { sameJson(expected.get(it), actual.get(it)) }
            }
            is JSONArray -> {
                assertTrue(actual is JSONArray)
                actual as JSONArray
                assertEquals(expected.length(), actual.length())
                (0 until expected.length()).forEach { sameJson(expected.get(it), actual.get(it)) }
            }
            is Number -> {
                assertTrue(actual is Number)
                assertEquals(expected.toLong(), (actual as Number).toLong())
            }
            else -> assertEquals(expected, actual)
        }
    }
    private fun writeProof(name: String, json: String) {
        proof.mkdirs()
        File(proof, name).writeText(json)
    }

    @Test fun sharedFixturesAndPythonProducedJsonRoundTrip() {
        val shared = File(fixtures, "canonical-v1.json").readText()
        val python = File(proof, "python-origin.json")
        val input = if (python.exists()) python.readText() else shared
        sameJson(JSONObject(shared), JSONObject(input))
        val tasks = TaskJsonCodec.decode(input)
        assertEquals(TaskState.entries.toSet(), tasks.map { it.state }.toSet())
        assertNull(tasks[0].importance)
        assertNull(tasks[0].urgency)
        assertEquals(9, tasks[1].importance)
        assertNull(tasks[1].urgency)
        assertNull(tasks[2].importance)
        assertEquals(7, tasks[2].urgency)
        assertEquals(listOf("active", "external:synthetic"), tasks[3].dependencyIds)
        assertEquals(listOf("meeting:synthetic-1", "decision:synthetic-2"), tasks[3].sourceRefs)
        assertEquals(listOf("artifact:synthetic-verified"), tasks[5].completionEvidence)
        val encoded = TaskJsonCodec.encode(tasks)
        sameJson(JSONObject(shared), JSONObject(encoded))
        sameJson(JSONObject(encoded), JSONObject(TaskJsonCodec.encode(TaskJsonCodec.decode(encoded))))
        writeProof("canonical-v1.json", encoded)
    }

    @Test fun androidOriginProducesEquivalentCanonicalJson() {
        val task = TaskRecord("android-origin", "Android-origin café", TaskState.DONE,
            urgency = 7, dependencyIds = listOf("active"), sourceRefs = listOf("source:synthetic"),
            completionEvidence = listOf("artifact:synthetic"))
        val json = TaskJsonCodec.encode(listOf(task))
        sameJson(JSONObject(File(fixtures, "android-origin.json").readText()), JSONObject(json))
        writeProof("android-origin.json", json)
    }

    @Test fun doneCannotBeConstructedOrCopiedWithoutEvidence() {
        reject { TaskRecord("T", "Task", TaskState.DONE) }
        reject { TaskRecord.create("Task", state = TaskState.DONE) }
        // A completion timestamp never substitutes for evidence.
        reject { TaskRecord("T", "Task", TaskState.DONE, completedAt = 200) }
        val task = TaskRecord.create("Task", now = 100)
        reject { task.copy(state = TaskState.DONE) }
        reject { task.withCompletion(true, now = 200) }
        for (evidence in listOf(listOf(""), listOf(" \t\n"), listOf("valid", " "))) {
            reject { task.withCompletion(true, now = 200, evidence = evidence) }
        }
        val done = task.withCompletion(true, now = 200, evidence = listOf("proof:1"))
        assertEquals(TaskState.DONE, done.state)
        assertEquals(TaskState.ACTIVE, done.withCompletion(false, now = 300).state)
    }

    @Test fun referencesAreDefensiveAndPrioritiesIndependent() {
        val evidence = mutableListOf("proof:1")
        val done = TaskRecord("T", "Task", TaskState.DONE, completionEvidence = evidence)
        evidence.clear()
        assertEquals(listOf("proof:1"), done.completionEvidence)
        try { (done.completionEvidence as MutableList<String>).clear(); fail("Mutable evidence") }
        catch (_: UnsupportedOperationException) { }
        val task = TaskRecord("A", "Task", TaskState.ACTIVE, importance = 9)
        assertNull(task.urgency)
        reject { task.copy(dependencyIds = listOf("A")) }
        reject { task.copy(sourceRefs = listOf(" ")) }
        reject { task.copy(importance = 0) }
        reject { task.copy(urgency = 11) }
        reject { TaskState.valueOf("CANCELLED") }
        TaskState.entries.filter { it != TaskState.DONE }.forEach { task.copy(state = it) }
    }

    @Test fun canonicalImportRejectsInvalidDoneAndMalformedTypes() {
        val root = JSONObject(File(fixtures, "canonical-v1.json").readText())
        val task = root.getJSONArray("tasks").getJSONObject(0)
        for (evidence in listOf(JSONArray(), JSONArray().put(" "), JSONArray().put("valid").put(""))) {
            task.put("state", "DONE").put("completion_evidence", evidence)
            reject { TaskJsonCodec.decode(root.toString()) }
        }
        task.put("state", "ACTIVE").put("completion_evidence", JSONArray())
        for (score in listOf<Any>(true, "9", 9.5, 11)) {
            task.put("importance", score)
            reject { TaskJsonCodec.decode(root.toString()) }
        }
        task.put("importance", JSONObject.NULL).put("state", "ARCHIVED")
        reject { TaskJsonCodec.decode(root.toString()) }
        task.put("state", "ACTIVE").put("source_refs", JSONArray().put(false))
        reject { TaskJsonCodec.decode(root.toString()) }
    }

    @Test fun duplicateIdsAndUnsupportedVersionFail() {
        val root = JSONObject(File(fixtures, "canonical-v1.json").readText())
        root.getJSONArray("tasks").put(root.getJSONArray("tasks").getJSONObject(0))
        reject { TaskJsonCodec.decode(root.toString()) }
        for (version in listOf<Any>(true, "1", 2)) {
            root.put("schema_version", version)
            reject { TaskJsonCodec.decode(root.toString()) }
        }
    }

    @Test fun legacyMigrationPreservesClientFieldsAndTimestamps() {
        val old = File(fixtures, "android-v01.json").readText()
        val encoded = TaskJsonCodec.encode(TaskJsonCodec.decode(old))
        sameJson(JSONObject(File(fixtures, "android-v01-expected.json").readText()), JSONObject(encoded))
        writeProof("android-v01-expected.json", encoded)
    }

    @Test fun legacyUnprovedDoneCarriesOriginalForReconciliation() {
        val old = JSONObject(File(fixtures, "android-v01.json").readText())
        old.getJSONArray("tasks").getJSONObject(0).put("state", "DONE").put("completedAt", 1700000001000)
        val original = old.toString(2)
        try {
            TaskJsonCodec.decode(original)
            fail("Unproved historical DONE accepted")
        } catch (error: LegacyReconciliationRequired) {
            assertEquals(listOf("legacy-task"), error.taskIds)
            assertEquals(original, error.originalPayload)
        }
        old.getJSONArray("tasks").getJSONObject(0).put("completionEvidence", JSONArray().put("proof:legacy"))
        assertEquals(TaskState.DONE, TaskJsonCodec.decode(old.toString()).single().state)
        old.getJSONArray("tasks").getJSONObject(0).put("completionEvidence", JSONArray().put(" "))
        reject { TaskJsonCodec.decode(old.toString()) }
    }
}
