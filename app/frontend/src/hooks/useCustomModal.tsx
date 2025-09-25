import { useState, useCallback } from 'react';
import CustomModal from '../components/CustomModal/index.tsx';

interface ModalConfig {
  title: string;
  content: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'confirm' | 'info' | 'warning' | 'error';
  onConfirm?: () => void;
  onCancel?: () => void;
}

export const useCustomModal = () => {
  const [modalConfig, setModalConfig] = useState<ModalConfig | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const showModal = useCallback((config: ModalConfig) => {
    setModalConfig(config);
    setIsOpen(true);
  }, []);

  const hideModal = useCallback(() => {
    setIsOpen(false);
    setTimeout(() => {
      setModalConfig(null);
    }, 300);
  }, []);

  const handleConfirm = useCallback(() => {
    if (modalConfig?.onConfirm) {
      modalConfig.onConfirm();
    }
    hideModal();
  }, [modalConfig, hideModal]);

  const handleCancel = useCallback(() => {
    if (modalConfig?.onCancel) {
      modalConfig.onCancel();
    }
    hideModal();
  }, [modalConfig, hideModal]);

  const Modal = modalConfig ? (
    <CustomModal
      isOpen={isOpen}
      title={modalConfig.title}
      content={modalConfig.content}
      confirmText={modalConfig.confirmText}
      cancelText={modalConfig.cancelText}
      type={modalConfig.type}
      onConfirm={modalConfig.onConfirm ? handleConfirm : undefined}
      onClose={handleCancel}
    />
  ) : null;

  return {
    showModal,
    hideModal,
    Modal,
    confirm: (config: Omit<ModalConfig, 'type'>) => 
      showModal({ ...config, type: 'confirm' }),
    info: (config: Omit<ModalConfig, 'type'>) => 
      showModal({ ...config, type: 'info' }),
    warning: (config: Omit<ModalConfig, 'type'>) => 
      showModal({ ...config, type: 'warning' }),
    error: (config: Omit<ModalConfig, 'type'>) => 
      showModal({ ...config, type: 'error' }),
  };
};
