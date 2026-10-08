package za.co.davidbarske.basil.core

import androidx.compose.runtime.structuralEqualityPolicy
import org.junit.Assert.*
import org.junit.Test
import za.co.davidbarske.basil.data.TaskJsonCodec
import za.co.davidbarske.basil.ui.TaskUiState

class TaskRecordValueTest {
    private fun task() = TaskRecord("T", "Value task", TaskState.DONE, importance = 9,
        project = "Client project", updatedAt = 100, dependencyIds = listOf("D"),
        sourceRefs = listOf("source:synthetic"), completionEvidence = listOf("proof:synthetic"))

    @Test fun equalityHashAndStringAreStructural() {
        val task = task()
        val copy = task.copy()
        assertNotSame(task, copy)
        assertEquals(task, copy)
        assertEquals(copy, task)
        assertEquals(task.hashCode(), copy.hashCode())
        assertEquals(task.toString(), copy.toString())
        assertTrue(task.toString().contains("completionEvidence=[proof:synthetic]"))
        assertNotEquals(task, task.copy(description = "Changed"))
        assertNotEquals(task, task.copy(notes = "Changed client metadata"))
        assertNotEquals(task, task.copy(updatedAt = 101))
        assertNotEquals(task, "T")
        assertEquals(1, setOf(task, copy).size)
        assertEquals("value", mapOf(task to "value")[copy])
    }

    @Test fun everyCanonicalFieldParticipatesInComparison() {
        val task = task()
        val changes = listOf(task.copy(id = "Other"), task.copy(description = "Other"),
            task.copy(state = TaskState.MONITOR), task.copy(importance = null), task.copy(urgency = 7),
            task.copy(owner = "Explicit owner"), task.copy(deadline = "Explicit deadline"),
            task.copy(dependencyIds = listOf("Other")), task.copy(sourceRefs = listOf("other:source")),
            task.copy(completionEvidence = listOf("other:proof")))
        changes.forEach { assertFalse(task.sameCanonicalContent(it)); assertNotEquals(task, it) }
        val metadataOnly = task.copy(project = "Other", nextAction = "Other", notes = "Other",
            createdAt = 1, updatedAt = 200, completedAt = 200)
        assertTrue(task.sameCanonicalContent(metadataOnly))
        assertNotEquals(task, metadataOnly)
    }

    @Test fun callerMutationCannotChangeValueOrHash() {
        val sources = mutableListOf("source:synthetic")
        val evidence = mutableListOf("proof:synthetic")
        val task = TaskRecord("T", "Task", TaskState.DONE, sourceRefs = sources, completionEvidence = evidence)
        val before = task.copy()
        val hash = task.hashCode()
        sources.clear()
        evidence.clear()
        assertEquals(before, task)
        assertEquals(hash, task.hashCode())
        try { (task.sourceRefs as MutableList<String>).clear(); fail("Mutable references") }
        catch (_: UnsupportedOperationException) { }
        try { task.copy(completionEvidence = listOf(" ")); fail("Invalid copied DONE") }
        catch (_: IllegalArgumentException) { }
    }

    @Test fun composeStateAndCodecRoundtripUseValueEquality() {
        val task = task()
        val state = TaskUiState(tasks = listOf(task), loading = false)
        val copy = state.copy(tasks = listOf(task.copy()))
        assertEquals(state, copy)
        assertTrue(structuralEqualityPolicy<TaskUiState>().equivalent(state, copy))
        assertFalse(structuralEqualityPolicy<TaskUiState>().equivalent(
            state, state.copy(tasks = listOf(task.copy(description = "Changed")))))
        val decoded = TaskJsonCodec.decode(TaskJsonCodec.encode(listOf(task))).single()
        // Effective sidecar presence, not a constructor flag, defines represented equality.
        assertEquals(task, decoded)
        assertEquals(task.hashCode(), decoded.hashCode())
        assertNotEquals(TaskRecord("A", "Task", TaskState.ACTIVE),
            TaskRecord("A", "Task", TaskState.ACTIVE, hasClientMetadata = true))
    }
}
