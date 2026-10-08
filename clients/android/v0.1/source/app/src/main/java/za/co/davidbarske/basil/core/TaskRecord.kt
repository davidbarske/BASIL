package za.co.davidbarske.basil.core

import java.util.Collections
import java.util.UUID

enum class TaskState(val label: String) {
    ACTIVE("Active"), WAITING("Waiting"), SCHEDULED("Scheduled"),
    BLOCKED("Blocked"), MONITOR("Monitor"), DONE("Done")
}

/** Canonical commitment fields; presentation/timestamps remain client metadata.
 * Defensive lists prevent caller mutation from undoing validation.
 */
class TaskRecord(
    val id: String, val description: String, val state: TaskState,
    val project: String = "", val nextAction: String = "", val deadline: String? = null,
    val notes: String = "", val createdAt: Long? = null, val updatedAt: Long? = null,
    val completedAt: Long? = null, val importance: Int? = null, val urgency: Int? = null,
    val owner: String? = null, dependencyIds: List<String> = emptyList(),
    sourceRefs: List<String> = emptyList(), completionEvidence: List<String> = emptyList(),
    val hasClientMetadata: Boolean = false
) {
    val dependencyIds: List<String> = Collections.unmodifiableList(ArrayList(dependencyIds))
    val sourceRefs: List<String> = Collections.unmodifiableList(ArrayList(sourceRefs))
    val completionEvidence: List<String> = Collections.unmodifiableList(ArrayList(completionEvidence))
    init {
        require(id.isNotBlank()) { "Task id cannot be blank." }
        require(description.isNotBlank()) { "Task description cannot be blank." }
        require(importance == null || importance in 1..10) { "Importance must be 1..10 or unknown." }
        require(urgency == null || urgency in 1..10) { "Urgency must be 1..10 or unknown." }
        require(owner == null || owner.isNotBlank()) { "Owner must be absent or nonblank." }
        require(deadline == null || deadline.isNotBlank()) { "Deadline must be absent or nonblank." }
        require((this.dependencyIds + this.sourceRefs + this.completionEvidence).all { it.isNotBlank() }) {
            "References must be nonblank."
        }
        require(id !in this.dependencyIds) { "A task cannot depend on itself." }
        require(state != TaskState.DONE || this.completionEvidence.isNotEmpty()) {
            "DONE requires explicit nonblank completion evidence."
        }
        require(listOf(createdAt, updatedAt, completedAt).all { it == null || it >= 0 }) {
            "Client timestamps must be nonnegative epoch milliseconds or unknown."
        }
    }


    /** Equality includes every represented field, including client metadata.
     * Canonical import comparison deliberately excludes that metadata.
     */
    private data class CanonicalValue(
        val id: String, val description: String, val state: TaskState,
        val importance: Int?, val urgency: Int?, val owner: String?, val deadline: String?,
        val dependencyIds: List<String>, val sourceRefs: List<String>, val completionEvidence: List<String>
    )
    private data class ClientValue(
        val project: String, val nextAction: String, val notes: String,
        val createdAt: Long?, val updatedAt: Long?, val completedAt: Long?, val present: Boolean
    )
    val carriesClientMetadata: Boolean
        get() = hasClientMetadata || listOf(project, nextAction, notes).any { it.isNotEmpty() } ||
            listOf(createdAt, updatedAt, completedAt).any { it != null }

    private fun canonicalValue() = CanonicalValue(id, description, state, importance, urgency,
        owner, deadline, dependencyIds, sourceRefs, completionEvidence)
    private fun clientValue() = ClientValue(project, nextAction, notes,
        createdAt, updatedAt, completedAt, carriesClientMetadata)

    fun sameCanonicalContent(other: TaskRecord): Boolean = canonicalValue() == other.canonicalValue()
    override fun equals(other: Any?): Boolean =
        other is TaskRecord && canonicalValue() == other.canonicalValue() && clientValue() == other.clientValue()
    override fun hashCode(): Int = 31 * canonicalValue().hashCode() + clientValue().hashCode()
    override fun toString(): String = "TaskRecord(canonical=${canonicalValue()}, client=${clientValue()})"

    fun copy(
        id: String = this.id, description: String = this.description, state: TaskState = this.state,
        project: String = this.project, nextAction: String = this.nextAction,
        deadline: String? = this.deadline, notes: String = this.notes,
        createdAt: Long? = this.createdAt, updatedAt: Long? = this.updatedAt,
        completedAt: Long? = this.completedAt, importance: Int? = this.importance,
        urgency: Int? = this.urgency, owner: String? = this.owner,
        dependencyIds: List<String> = this.dependencyIds, sourceRefs: List<String> = this.sourceRefs,
        completionEvidence: List<String> = this.completionEvidence,
        hasClientMetadata: Boolean = this.hasClientMetadata
    ) = TaskRecord(id, description, state, project, nextAction, deadline, notes,
        createdAt, updatedAt, completedAt, importance, urgency, owner, dependencyIds,
        sourceRefs, completionEvidence, hasClientMetadata)

    fun withCompletion(
        done: Boolean, now: Long = System.currentTimeMillis(), evidence: List<String> = emptyList()
    ) = copy(state = if (done) TaskState.DONE else TaskState.ACTIVE,
        updatedAt = now, completedAt = if (done) now else null,
        completionEvidence = if (done) evidence else emptyList())

    companion object {
        fun create(
            description: String, state: TaskState = TaskState.ACTIVE,
            project: String = "", nextAction: String = "", deadline: String? = null,
            notes: String = "", now: Long = System.currentTimeMillis(),
            completionEvidence: List<String> = emptyList()
        ) = TaskRecord(
            id = UUID.randomUUID().toString(), description = description.trim(), state = state,
            project = project.trim(), nextAction = nextAction.trim(),
            deadline = deadline?.trim()?.takeIf { it.isNotBlank() }, notes = notes.trim(),
            createdAt = now, updatedAt = now, completedAt = if (state == TaskState.DONE) now else null,
            completionEvidence = completionEvidence, hasClientMetadata = true
        )
    }
}
