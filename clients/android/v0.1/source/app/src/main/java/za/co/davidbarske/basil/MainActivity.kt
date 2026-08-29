package za.co.davidbarske.basil

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import za.co.davidbarske.basil.ui.BasilApp
import za.co.davidbarske.basil.ui.BasilTheme
import za.co.davidbarske.basil.ui.TaskViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            BasilTheme {
                val taskViewModel: TaskViewModel = viewModel(
                    factory = TaskViewModel.factory(applicationContext)
                )
                BasilApp(taskViewModel)
            }
        }
    }
}
