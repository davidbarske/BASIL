package za.co.davidbarske.basil.ui

import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import za.co.davidbarske.basil.core.TaskRecord
import za.co.davidbarske.basil.core.TaskState

@Composable
fun BasilApp(viewModel: TaskViewModel) {
    val context = LocalContext.current
    val state = viewModel.uiState
    var query by remember { mutableStateOf("") }
    var editorTask by remember { mutableStateOf<TaskRecord?>(null) }
    var editorOpen by remember { mutableStateOf(false) }
    var pendingDelete by remember { mutableStateOf<TaskRecord?>(null) }

    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) {
            runCatching {
                context.contentResolver.openOutputStream(uri)?.use { stream ->
                    stream.write(viewModel.exportJson().toByteArray(Charsets.UTF_8))
                } ?: error("Unable to open export destination.")
            }.onSuccess {
                Toast.makeText(context, "BASIL export saved.", Toast.LENGTH_SHORT).show()
            }.onFailure {
                Toast.makeText(context, it.message ?: "Export failed.", Toast.LENGTH_LONG).show()
            }
        }
    }

    val importLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            runCatching {
                context.contentResolver.openInputStream(uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
                    ?: error("Unable to open selected file.")
            }.onSuccess(viewModel::importJson)
                .onFailure {
                    Toast.makeText(context, it.message ?: "Import failed.", Toast.LENGTH_LONG).show()
                }
        }
    }

    LaunchedEffect(state.message, state.error) {
        val message = state.error ?: state.message
        if (!message.isNullOrBlank()) {
            Toast.makeText(context, message, Toast.LENGTH_LONG).show()
            viewModel.clearMessage()
        }
    }

    if (editorOpen) {
        TaskEditorScreen(
            initial = editorTask,
            onCancel = {
                editorOpen = false
                editorTask = null
            },
            onSave = { task ->
                viewModel.save(task)
                editorOpen = false
                editorTask = null
            }
        )
        return
    }

    val filteredTasks = remember(state.tasks, query) {
        val needle = query.trim().lowercase()
        if (needle.isBlank()) state.tasks else state.tasks.filter { task ->
            listOf(task.description, task.project, task.nextAction, task.notes, task.state.label)
                .any { it.lowercase().contains(needle) }
        }
    }

    Scaffold(
        topBar = {
            BasilTopBar(
                onImport = { importLauncher.launch(arrayOf("application/json", "text/plain")) },
                onExport = { exportLauncher.launch("BASIL_tasks_v0.1.json") }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = {
                    editorTask = null
                    editorOpen = true
                }
            ) {
                Text("+", style = MaterialTheme.typography.headlineMedium)
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
        ) {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Search tasks") }
            )

            Spacer(Modifier.height(12.dp))

            when {
                state.loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }

                filteredTasks.isEmpty() -> EmptyTasks(query.isNotBlank())

                else -> LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(filteredTasks, key = { it.id }) { task ->
                        TaskCard(
                            task = task,
                            onEdit = {
                                editorTask = task
                                editorOpen = true
                            },
                            onToggleDone = { viewModel.toggleDone(task) },
                            onDelete = { pendingDelete = task }
                        )
                    }
                    item { Spacer(Modifier.height(88.dp)) }
                }
            }
        }
    }

    pendingDelete?.let { task ->
        AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("Delete task?") },
            text = {
                Text("This permanently removes the task from BASIL v0.1. Export first if you need an external backup.")
            },
            confirmButton = {
                Button(onClick = {
                    viewModel.delete(task.id)
                    pendingDelete = null
                }) { Text("Delete") }
            },
            dismissButton = {
                TextButton(onClick = { pendingDelete = null }) { Text("Cancel") }
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BasilTopBar(onImport: () -> Unit, onExport: () -> Unit) {
    TopAppBar(
        title = {
            Column {
                Text("BASIL", fontWeight = FontWeight.Bold)
                Text("v0.1 · Local task register", style = MaterialTheme.typography.labelSmall)
            }
        },
        actions = {
            TextButton(onClick = onImport) { Text("Import") }
            TextButton(onClick = onExport) { Text("Export") }
        }
    )
}

@Composable
private fun EmptyTasks(searching: Boolean) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                if (searching) "No matching tasks." else "No tasks yet.",
                style = MaterialTheme.typography.titleMedium
            )
            if (!searching) {
                Text(
                    "Use + to create BASIL's first live task.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun TaskCard(
    task: TaskRecord,
    onEdit: () -> Unit,
    onToggleDone: () -> Unit,
    onDelete: () -> Unit
) {
    Card(onClick = onEdit) {
        Column(Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    task.state.label.uppercase(),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary
                )
                if (task.project.isNotBlank()) {
                    Text(
                        task.project,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }

            Spacer(Modifier.height(8.dp))
            Text(
                task.description,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )

            if (task.nextAction.isNotBlank()) {
                Spacer(Modifier.height(8.dp))
                Text("Next: ${task.nextAction}", style = MaterialTheme.typography.bodyMedium)
            }

            task.deadline?.let {
                Spacer(Modifier.height(4.dp))
                Text(
                    "Deadline: $it",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                TextButton(onClick = onToggleDone) {
                    Text(if (task.completedAt == null) "Done" else "Reopen")
                }
                TextButton(onClick = onEdit) { Text("Edit") }
                TextButton(onClick = onDelete) { Text("Delete") }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TaskEditorScreen(
    initial: TaskRecord?,
    onCancel: () -> Unit,
    onSave: (TaskRecord) -> Unit
) {
    var description by remember(initial?.id) { mutableStateOf(initial?.description ?: "") }
    var project by remember(initial?.id) { mutableStateOf(initial?.project ?: "") }
    var nextAction by remember(initial?.id) { mutableStateOf(initial?.nextAction ?: "") }
    var deadline by remember(initial?.id) { mutableStateOf(initial?.deadline ?: "") }
    var notes by remember(initial?.id) { mutableStateOf(initial?.notes ?: "") }
    var selectedState by remember(initial?.id) { mutableStateOf(initial?.state ?: TaskState.ACTIVE) }
    var stateMenuOpen by remember { mutableStateOf(false) }
    var validationError by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (initial == null) "New task" else "Edit task") },
                navigationIcon = {
                    TextButton(onClick = onCancel) { Text("Back") }
                },
                actions = {
                    TextButton(
                        onClick = {
                            val clean = description.trim()
                            if (clean.isBlank()) {
                                validationError = "Description is required."
                                return@TextButton
                            }

                            val now = System.currentTimeMillis()
                            val task = if (initial == null) {
                                TaskRecord.create(
                                    description = clean,
                                    state = selectedState,
                                    project = project,
                                    nextAction = nextAction,
                                    deadline = deadline,
                                    notes = notes,
                                    now = now
                                )
                            } else {
                                initial.copy(
                                    description = clean,
                                    state = selectedState,
                                    project = project.trim(),
                                    nextAction = nextAction.trim(),
                                    deadline = deadline.trim().takeIf { it.isNotBlank() },
                                    notes = notes.trim(),
                                    updatedAt = now,
                                    completedAt = when {
                                        selectedState == TaskState.DONE && initial.completedAt == null -> now
                                        selectedState != TaskState.DONE -> null
                                        else -> initial.completedAt
                                    }
                                )
                            }
                            onSave(task)
                        }
                    ) { Text("Save") }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Spacer(Modifier.height(4.dp))
                OutlinedTextField(
                    value = description,
                    onValueChange = {
                        description = it
                        validationError = null
                    },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Description *") },
                    minLines = 2,
                    isError = validationError != null,
                    supportingText = validationError?.let { message -> { Text(message) } }
                )
            }

            item {
                ExposedDropdownMenuBox(
                    expanded = stateMenuOpen,
                    onExpandedChange = { stateMenuOpen = !stateMenuOpen }
                ) {
                    OutlinedTextField(
                        value = selectedState.label,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("State") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = stateMenuOpen) },
                        modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = stateMenuOpen,
                        onDismissRequest = { stateMenuOpen = false }
                    ) {
                        TaskState.entries.forEach { state ->
                            DropdownMenuItem(
                                text = { Text(state.label) },
                                onClick = {
                                    selectedState = state
                                    stateMenuOpen = false
                                }
                            )
                        }
                    }
                }
            }

            item {
                OutlinedTextField(
                    value = project,
                    onValueChange = { project = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Project / workstream") },
                    singleLine = true
                )
            }

            item {
                OutlinedTextField(
                    value = nextAction,
                    onValueChange = { nextAction = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Next action") },
                    minLines = 2
                )
            }

            item {
                OutlinedTextField(
                    value = deadline,
                    onValueChange = { deadline = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Deadline") },
                    placeholder = { Text("Only if real, e.g. 2026-08-27 14:00") },
                    singleLine = true
                )
            }

            item {
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Notes") },
                    minLines = 4
                )
            }

            item {
                Text(
                    "v0.1 stores deadline text exactly as entered. Temporal scoring is deliberately deferred to a later BASIL module.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(32.dp))
            }
        }
    }
}
