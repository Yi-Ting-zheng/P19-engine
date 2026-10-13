-- Specimen-001: negative control fixture (declared build exit=1, NOT locally built)
-- P0 状态脚本标本：真实构建失败状态由 specimen.yaml machine.build_exit_code 声明。
theorem symbol_error_demo : True := by
  sorry

-- declared build log note: error: unbound variable 'x_0'
