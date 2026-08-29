package za.co.davidbarske.basil.ui

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.data.JsonTaskRepository
import za.co.davidbarske.basil.data.TaskJsonCodec
import za.co.davidbarske.basil.data.TaskRepository

data class TaskUiState(
    val tasks: List<TaskRecord> = emptyList(),
    val loading: Boolean = true,
    val message: String? = null,
    val error: String? = null
)

class TaskViewModel(private val repository: TaskRepository) : ViewModel() {
    var uiState by mutableStateOf(TaskUiState())
        private set

    init {
        reload()
    }

    fun reload() {
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { repository.loadAll() }
                .onSuccess { tasks ->
                    withContext(Dispatchers.Main) {
                        uiState = uiState.copy(
                            tasks = sort(tasks),
                            loading = false,
                            error = null
                        )
                    }
                }
                .onFailure { error ->
                    withContext(Dispatchers.Main) {
                        uiState = uiState.copy(
                            loading = false,
                            error = error.message ?: "Unable to read BASIL task data."
                        )
                    }
                }
        }
    }

    fun save(task: TaskRecord) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { repository.upsert(task) }
                .onSuccess {
                    val tasks = repository.loadAll()
                    withContext(Dispatchers.Main) {
                        uiState = uiState.copy(
                            tasks = sort(tasks),
                            message = "Task saved.",
                            error = null
                        )
                    }
                }
                .onFailure { reportFailure(it, "Unable to save task.") }
        }
    }

    fun delete(taskId: String) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { repository.delete(taskId) }
                .onSuccess {
                    val tasks = repository.loadAll()
                    withContext(Dispatchers.Main) {
                        uiState = uiState.copy(
                            tasks = sort(tasks),
                            message = "Task deleted.",
                            error = null
                        )
                    }
                }
                .onFailure { reportFailure(it, "Unable to delete task.") }
        }
    }

    fun toggleDone(task: TaskRecord) {
        save(task.withCompletion(task.completedAt == null))
    }

    fun exportJson(): String = TaskJsonCodec.encode(uiState.tasks)

    fun importJson(text: String) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatching {
                val imported = TaskJsonCodec.decode(text)
                val existing = repository.loadAll().associateBy { it.id }.toMutableMap()
                imported.forEach { candidate ->
                    val current = existing[candidate.id]
                    if (current == null || candidate.updatedAt >= current.updatedAt) {
                        existing[candidate.id] = candidate
                    }
                }
                repository.replaceAll(existing.values.toList())
                repository.loadAll()
            }.onSuccess { tasks ->
                withContext(Dispatchers.Main) {
                    uiState = uiState.copy(
                        tasks = sort(tasks),
                        message = "Import complete. Existing data was preserved and merged by task ID.",
                        error = null
                    )
                }
            }.onFailure { reportFailure(it, "Import failed.") }
        }
    }

    fun clearMessage() {
        uiState = uiState.copy(message = null, error = null)
    }

    private suspend fun reportFailure(error: Throwable, fallback: String) {
        withContext(Dispatchers.Main) {
            uiState = uiState.copy(error = error.message ?: fallback)
        }
    }

    private fun sort(tasks: List<TaskRecord>): List<TaskRecord> = tasks.sortedWith(
        compareBy<TaskRecord> { it.completedAt != null }
            .thenByDescending { it.updatedAt }
    )

    companion object {
        fun factory(context: Context) = viewModelFactory {
            initializer {
                TaskViewModel(JsonTaskRepository(context.applicationContext))
            }
        }
    }
}
