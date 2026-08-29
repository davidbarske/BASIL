package za.co.davidbarske.basil.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val BasilDark = darkColorScheme(
    primary = Color(0xFF8CB8E8),
    onPrimary = Color(0xFF07111F),
    primaryContainer = Color(0xFF17385E),
    onPrimaryContainer = Color(0xFFD9E9FA),
    secondary = Color(0xFF71C7C2),
    background = Color(0xFF07111F),
    onBackground = Color(0xFFE6EDF5),
    surface = Color(0xFF0C1827),
    onSurface = Color(0xFFE6EDF5),
    surfaceVariant = Color(0xFF132338),
    onSurfaceVariant = Color(0xFFB8C7D9),
    outline = Color(0xFF40556D),
    error = Color(0xFFFFB4AB)
)

@Composable
fun BasilTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = BasilDark,
        content = content
    )
}
