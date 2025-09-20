import { Modal } from 'antd';
import type { ModalFuncProps } from 'antd';

// 创建一个带有正确z-index的Modal容器
const createModalContainer = (): HTMLElement => {
  const modalRoot = document.createElement('div');
  modalRoot.className = 'modal-fix-container';
  modalRoot.style.position = 'fixed';
  modalRoot.style.top = '0';
  modalRoot.style.left = '0';
  modalRoot.style.width = '100%';
  modalRoot.style.height = '100%';
  modalRoot.style.zIndex = '99999';
  modalRoot.style.pointerEvents = 'none';
  document.body.appendChild(modalRoot);
  return modalRoot;
};

// 清理Modal容器
const cleanupModalContainer = (container: HTMLElement) => {
  if (container && container.parentNode) {
    container.parentNode.removeChild(container);
  }
};

// 通用的Modal配置增强函数
const enhanceModalConfig = (config: ModalFuncProps): ModalFuncProps => {
  const container = createModalContainer();
  
  const originalAfterClose = config.afterClose;
  const originalOnOk = config.onOk;
  const originalOnCancel = config.onCancel;

  return {
    ...config,
    zIndex: 100000,
    maskClosable: false,
    centered: true,
    getContainer: () => container,
    afterClose: () => {
      cleanupModalContainer(container);
      if (originalAfterClose) {
        originalAfterClose();
      }
    },
    onOk: (...args) => {
      const result = originalOnOk ? originalOnOk(...args) : undefined;
      // 如果onOk返回Promise，等待完成后再清理
      if (result instanceof Promise) {
        return result.finally(() => {
          // 延迟清理，让Modal有时间关闭动画
          setTimeout(() => cleanupModalContainer(container), 300);
        });
      }
      // 延迟清理，让Modal有时间关闭动画
      setTimeout(() => cleanupModalContainer(container), 300);
      return result;
    },
    onCancel: (...args) => {
      const result = originalOnCancel ? originalOnCancel(...args) : undefined;
      // 延迟清理，让Modal有时间关闭动画
      setTimeout(() => cleanupModalContainer(container), 300);
      return result;
    }
  };
};

// 修复后的Modal方法
export const FixedModal = {
  confirm: (config: ModalFuncProps) => {
    try {
      return Modal.confirm(enhanceModalConfig(config));
    } catch (error) {
      console.error('FixedModal.confirm 失败，使用原生确认:', error);
      // 降级到原生确认对话框
      const title = typeof config.title === 'string' ? config.title : '确认';
      const content = typeof config.content === 'string' ? config.content : '';
      const confirmed = window.confirm(`${title}\n\n${content}`);
      if (confirmed && config.onOk) {
        config.onOk();
      }
    }
  },
  
  info: (config: ModalFuncProps) => {
    try {
      return Modal.info(enhanceModalConfig(config));
    } catch (error) {
      console.error('FixedModal.info 失败，使用原生弹窗:', error);
      // 降级到原生弹窗
      const title = typeof config.title === 'string' ? config.title : '信息';
      const content = typeof config.content === 'string' ? config.content : '';
      window.alert(`${title}\n\n${content}`);
    }
  },
  
  success: (config: ModalFuncProps) => {
    try {
      return Modal.success(enhanceModalConfig(config));
    } catch (error) {
      console.error('FixedModal.success 失败，使用原生弹窗:', error);
      const title = typeof config.title === 'string' ? config.title : '成功';
      const content = typeof config.content === 'string' ? config.content : '';
      window.alert(`${title}\n\n${content}`);
    }
  },
  
  error: (config: ModalFuncProps) => {
    try {
      return Modal.error(enhanceModalConfig(config));
    } catch (error) {
      console.error('FixedModal.error 失败，使用原生弹窗:', error);
      const title = typeof config.title === 'string' ? config.title : '错误';
      const content = typeof config.content === 'string' ? config.content : '';
      window.alert(`${title}\n\n${content}`);
    }
  },
  
  warning: (config: ModalFuncProps) => {
    try {
      return Modal.warning(enhanceModalConfig(config));
    } catch (error) {
      console.error('FixedModal.warning 失败，使用原生弹窗:', error);
      const title = typeof config.title === 'string' ? config.title : '警告';
      const content = typeof config.content === 'string' ? config.content : '';
      window.alert(`${title}\n\n${content}`);
    }
  }
};
