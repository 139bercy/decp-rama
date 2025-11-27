from general_process.GlobalProcess import GlobalProcess
import augmente.utils

suffixes = ['2024-01','2024-02','2024-03','2024-04','2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11','2024-12','2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07','2025-08','2025-09','2025-10','2025-11']
#suffixes = ['2025-09']
#suffixes = ['global']
gp = GlobalProcess('2022',None)
gp.upload_on_datagouv(suffixes)
