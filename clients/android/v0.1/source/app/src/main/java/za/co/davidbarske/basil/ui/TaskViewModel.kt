package za.co.davidbarske.basil.ui

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.data.CanonicalImportConflict
import za.co.davidbarske.basil.data.LocalSourceProblem
import za.co.davidbarske.basil.data.LocalSnapshot
import za.co.davidbarske.basil.data.JsonTaskRepository
import za.co.davidbarske.basil.data.TaskJsonCodec
import za.co.davidbarske.basil.data.TaskRepository

data class TaskUiState(
    val tasks: List<TaskRecord> = emptyList(),
    val loading: Boolean = true,
    val message: String? = null,
    val error: String? = null,
    val sourceProblem: LocalSourceProblem? = null,
    val importConflict: CanonicalImportConflict? = null
)

class TaskViewModel(
    private val repository: TaskRepository,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) : ViewModel() {
    var uiState by mutableStateOf(TaskUiState())
        private set

    init { reload() }

    private fun applySnapshot(snapshot: LocalSnapshot, message: String? = null) {
        uiState = uiState.copy(tasks = sort(snapshot.tasks), loading = false, error = null,
            message = message, sourceProblem = snapshot.sourceProblem)
    }

    fun reload() {
        viewModelScope.launch(ioDispatcher) {
            runCatching { repository.readSnapshot() }
                .onSuccess { snapshot -> withContext(Dispatchers.Main) { applySnapshot(snapshot) } }
                .onFailure { reportFailure(it, "Unable to read BASIL task data.") }
        }
    }

    fun save(task: TaskRecord) {
        viewModelScope.launch(ioDispatcher) {
            runCatching {
                repository.upsert(task)
                repository.readSnapshot()
            }.onSuccess { snapshot ->
                withContext(Dispatchers.Main) { applySnapshot(snapshot, "Task saved.") }
            }.onFailure { reportFailure(it, "Unable to save task.") }
        }
    }

    fun delete(taskId: String) {
        viewModelScope.launch(ioDispatcher) {
            runCatching {
                repository.delete(taskId)
                repository.readSnapshot()
            }.onSuccess { snapshot ->
                withContext(Dispatchers.Main) { applySnapshot(snapshot, "Task removed from this device only.") }
            }.onFailure { reportFailure(it, "Unable to remove local task.") }
        }
    }

    fun toggleDone(task: TaskRecord) {
        if (task.state != za.co.davidbarske.basil.core.TaskState.DONE) {
            uiState = uiState.copy(error = "Use Edit to supply completion evidence before marking DONE.")
        } else {
            save(task.withCompletion(false))
        }
    }

    fun exportBytes(): ByteArray = uiState.sourceProblem?.exportBytes()
        ?: TaskJsonCodec.encode(uiState.tasks).toByteArray(Charsets.UTF_8)

    fun exportConflictingImportBytes(): ByteArray =
        (uiState.importConflict ?: error("No conflicting import is available."))
            .originalPayload.toByteArray(Charsets.UTF_8)

    fun importJson(text: String) {
        viewModelScope.launch(ioDispatcher) {
            runCatching {
                repository.importJson(text)
                repository.readSnapshot()
            }.onSuccess { snapshot ->
                withContext(Dispatchers.Main) {
                    applySnapshot(snapshot, "Canonical imports merged. Identical IDs retain local client metadata.")
                    uiState = uiState.copy(importConflict = null)
                }
            }.onFailure { reportFailure(it, "Import failed.") }
        }
    }

    fun reconcileLocal(text: String) {
        viewModelScope.launch(ioDispatcher) {
            runCatching {
                repository.reconcileLocal(text)
                repository.readSnapshot()
            }.onSuccess { snapshot ->
                withContext(Dispatchers.Main) {
                    applySnapshot(snapshot, "Reconciled register loaded. Exact original source retained separately.")
                    uiState = uiState.copy(importConflict = null)
                }
            }.onFailure { reportFailure(it, "Historical source reconciliation failed.") }
        }
    }

    fun clearMessage() {
        uiState = uiState.copy(message = null, error = null)
    }

    private suspend fun reportFailure(error: Throwable, fallback: String) {
        withContext(Dispatchers.Main) {
            uiState = uiState.copy(loading = false, error = error.message ?: fallback,
                importConflict = if (error is CanonicalImportConflict) error else uiState.importConflict)
        }
    }

    private fun sort(tasks: List<TaskRecord>): List<TaskRecord> = tasks.sortedWith(
        compareBy<TaskRecord> { it.state == za.co.davidbarske.basil.core.TaskState.DONE }
            .thenByDescending { it.updatedAt }
    )

    companion object {
        fun factory(context: Context) = viewModelFactory {
            initializer { TaskViewModel(JsonTaskRepository(context.applicationContext)) }
        }
    }
}
