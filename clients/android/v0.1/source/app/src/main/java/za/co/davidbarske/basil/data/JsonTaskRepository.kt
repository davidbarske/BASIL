package za.co.davidbarske.basil.data

import android.content.Context
import za.co.davidbarske.basil.core.TaskRecord
import java.io.File
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.nio.file.StandardOpenOption

class JsonTaskRepository(private val directory: File) : TaskRepository {
    constructor(context: Context) : this(context.filesDir)
    private val dataFile = File(directory, "basil_tasks_v01.json")

    @Synchronized
    override fun readSnapshot(): LocalSnapshot =
        if (!dataFile.exists()) LocalSnapshot(emptyList()) else LocalRegister.inspect(dataFile.readBytes())

    @Synchronized
    override fun importJson(text: String) {
        val imported = TaskJsonCodec.decode(text)
        val merged = LocalRegister.merge(loadAll(), imported, text)
        writeAtomically(TaskJsonCodec.encode(merged))
    }

    @Synchronized
    override fun reconcileLocal(text: String) {
        require(dataFile.exists()) { "No local historical source exists." }
        val originalBytes = dataFile.readBytes()
        val original = originalBytes.decodeToString(throwOnInvalidSequence = true)
        val supplied = TaskJsonCodec.decode(text)
        val recovered = LocalRegister.reconcileLegacy(original, supplied)
        val encoded = TaskJsonCodec.encode(recovered)
        val retained = File(directory, "basil_tasks_v01.legacy-original.json")
        if (retained.exists()) {
            require(retained.readBytes().contentEquals(originalBytes)) {
                "A different original is already retained. Export it before reconciling this source."
            }
        } else {
            Files.write(retained.toPath(), originalBytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
        }
        writeAtomically(encoded)
    }

    @Synchronized
    override fun loadAll(): List<TaskRecord> {
        if (!dataFile.exists()) return emptyList()
        return TaskJsonCodec.decode(dataFile.readBytes().decodeToString(throwOnInvalidSequence = true))
    }

    @Synchronized
    override fun replaceAll(tasks: List<TaskRecord>) {
        loadAll() // Invalid/unreconciled local source must not be overwritten.
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    @Synchronized
    override fun upsert(task: TaskRecord) {
        val tasks = loadAll().toMutableList()
        val index = tasks.indexOfFirst { it.id == task.id }
        if (index >= 0) tasks[index] = task else tasks.add(task)
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    // Local-only deletion: never a canonical tombstone or permission to delete history.
    @Synchronized
    override fun delete(taskId: String) {
        val tasks = loadAll().filterNot { it.id == taskId }
        writeAtomically(TaskJsonCodec.encode(tasks))
    }

    private fun writeAtomically(text: String) {
        dataFile.parentFile?.mkdirs()
        val temp = File(dataFile.parentFile, "${dataFile.name}.tmp")
        temp.writeText(text, Charsets.UTF_8)

        try {
            Files.move(
                temp.toPath(),
                dataFile.toPath(),
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE
            )
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(temp.toPath(), dataFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
        }
    }
}
