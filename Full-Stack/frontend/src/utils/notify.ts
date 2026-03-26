import { ElMessage } from "element-plus";

export const notifySuccess = (message: string) => ElMessage.success(message);
export const notifyError = (message: string) => ElMessage.error(message);
export const notifyWarning = (message: string) => ElMessage.warning(message);
