package za.co.davidbarske.basil.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TaskRecordTest {
    @Test
    fun createTrimsFieldsAndDoesNotInventDeadline() {
        val task = TaskRecord.create(
            description = "  Review project material  ",
            project = " Project A ",
            nextAction = " Read document ",
            deadline = "   ",
            now = 100L
        )

        assertEquals("Review project material", task.description)
        assertEquals("Project A", task.project)
        assertEquals("Read document", task.nextAction)
        assertNull(task.deadline)
        assertEquals(TaskState.ACTIVE, task.state)
    }

    @Test
    fun completionAndReopenAreExplicitStateChanges() {
        val task = TaskRecord.create(description = "Task", now = 100L)
        val done = task.withCompletion(true, now = 200L)
        val reopened = done.withCompletion(false, now = 300L)

        assertEquals(TaskState.DONE, done.state)
        assertEquals(200L, done.completedAt)
        assertEquals(TaskState.ACTIVE, reopened.state)
        assertNull(reopened.completedAt)
        assertTrue(reopened.updatedAt > done.updatedAt)
    }
}
