package za.co.davidbarske.basil.ui

import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState
import za.co.davidbarske.basil.data.JsonTaskRepository
import za.co.davidbarske.basil.data.TaskJsonCodec

@OptIn(ExperimentalCoroutinesApi::class)
class TaskViewModelRecoveryTest {
    private val fixtures = File(System.getProperty("sybil.fixture.dir"))
    private fun historical(): ByteArray {
        val root = JSONObject(File(fixtures, "android-v01.json").readText())
        val visible = root.getJSONArray("tasks").getJSONObject(0)
        root.getJSONArray("tasks").put(JSONObject(visible.toString()).put("id", "unreconciled")
            .put("state", "DONE").put("completedAt", 1700000001000))
        return (root.toString(2) + "\r\n").toByteArray()
    }

    @Test fun startupShowsValidSubsetAndExportsOriginalDespiteReconciliationFailure() = runTest {
        val directory = Files.createTempDirectory("sybil-ui-recovery").toFile()
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        try {
            val bytes = historical()
            val file = File(directory, "basil_tasks_v01.json")
            file.writeBytes(bytes)
            val model = TaskViewModel(JsonTaskRepository(directory), StandardTestDispatcher(testScheduler))
            advanceUntilIdle()
            assertFalse(model.uiState.loading)
            assertEquals(listOf("legacy-task"), model.uiState.tasks.map { it.id })
            assertEquals(listOf("unreconciled"), model.uiState.sourceProblem!!.taskIds)
            assertArrayEquals(bytes, model.exportBytes())
            model.clearMessage()
            assertNotNull(model.uiState.sourceProblem)
            model.save(model.uiState.tasks.single().copy(description = "Must not overwrite source"))
            advanceUntilIdle()
            assertNotNull(model.uiState.error)
            assertArrayEquals(bytes, file.readBytes())
            assertArrayEquals(bytes, model.exportBytes())
        } finally { Dispatchers.resetMain(); directory.deleteRecursively() }
    }

    @Test fun explicitRecoveryRestoresOperationalViewAndRetainsExactHistoricalSource() = runTest {
        val directory = Files.createTempDirectory("sybil-ui-reconcile").toFile()
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        try {
            val bytes = historical()
            File(directory, "basil_tasks_v01.json").writeBytes(bytes)
            val model = TaskViewModel(JsonTaskRepository(directory), StandardTestDispatcher(testScheduler))
            advanceUntilIdle()
            val corrected = JSONObject(bytes.decodeToString())
            corrected.getJSONArray("tasks").getJSONObject(1)
                .put("completionEvidence", JSONArray().put("proof:explicit-synthetic-output"))
            model.reconcileLocal(corrected.toString())
            advanceUntilIdle()
            assertNull(model.uiState.sourceProblem)
            assertNull(model.uiState.error)
            assertEquals(2, model.uiState.tasks.size)
            assertEquals(TaskState.DONE, model.uiState.tasks.single { it.id == "unreconciled" }.state)
            assertEquals(2, TaskJsonCodec.decode(model.exportBytes().decodeToString()).size)
            assertArrayEquals(bytes, File(directory, "basil_tasks_v01.legacy-original.json").readBytes())
        } finally { Dispatchers.resetMain(); directory.deleteRecursively() }
    }

    @Test fun conflictingImportPreservesBothVariantsAndNeverChangesLocalRegister() = runTest {
        val directory = Files.createTempDirectory("sybil-ui-conflict").toFile()
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        try {
            val local = TaskRecord("same", "Local content", TaskState.ACTIVE, updatedAt = 100)
            val before = TaskJsonCodec.encode(listOf(local)).toByteArray()
            val file = File(directory, "basil_tasks_v01.json")
            file.writeBytes(before)
            val model = TaskViewModel(JsonTaskRepository(directory), StandardTestDispatcher(testScheduler))
            advanceUntilIdle()
            val candidate = local.copy(description = "Imported content", updatedAt = null)
            val originalImport = TaskJsonCodec.encode(listOf(candidate)) + "\n"
            model.importJson(originalImport)
            advanceUntilIdle()
            assertEquals(listOf(local), model.uiState.tasks)
            assertEquals(listOf("same"), model.uiState.importConflict!!.taskIds)
            assertEquals(listOf(local), model.uiState.importConflict!!.localTasks)
            assertEquals(listOf(candidate), model.uiState.importConflict!!.incomingTasks)
            assertArrayEquals(originalImport.toByteArray(), model.exportConflictingImportBytes())
            model.clearMessage()
            assertNotNull(model.uiState.importConflict)
            assertArrayEquals(before, file.readBytes())
            model.importJson(TaskJsonCodec.encode(listOf(local.copy(updatedAt = 999),
                TaskRecord("new", "Nonconflicting", TaskState.ACTIVE))))
            advanceUntilIdle()
            assertNull(model.uiState.importConflict)
            assertEquals(setOf("same", "new"), model.uiState.tasks.map { it.id }.toSet())
            assertEquals(local, model.uiState.tasks.single { it.id == "same" })
        } finally { Dispatchers.resetMain(); directory.deleteRecursively() }
    }

    @Test fun malformedLocalSourceStillHasAnExactExportPath() = runTest {
        val directory = Files.createTempDirectory("sybil-ui-malformed").toFile()
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        try {
            val bytes = "{ invalid JSON".toByteArray()
            val file = File(directory, "basil_tasks_v01.json")
            file.writeBytes(bytes)
            val model = TaskViewModel(JsonTaskRepository(directory), StandardTestDispatcher(testScheduler))
            advanceUntilIdle()
            assertFalse(model.uiState.loading)
            assertTrue(model.uiState.tasks.isEmpty())
            assertFalse(model.uiState.sourceProblem!!.legacyReconciliation)
            assertArrayEquals(bytes, model.exportBytes())
            assertArrayEquals(bytes, file.readBytes())
        } finally { Dispatchers.resetMain(); directory.deleteRecursively() }
    }
}
