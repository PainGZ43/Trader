    def cancel_training(self):
        """AI 학습 중단"""
        self.training_cancel_flag = True
        self.train_stop_btn.setEnabled(False)
        self.train_result_text.append("\n⏹️ 학습 중단 중...\n")
        self.log("⏹️ AI 학습 중단 요청")
    
    def _finish_training(self, success):
        """학습 완료 후 UI 복원"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        if not success:
            self.train_progress.setVisible(False)
