import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import './styles.css';

interface CustomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm?: () => void;
  title: string;
  content: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'confirm' | 'info' | 'warning' | 'error';
}

const CustomModal: React.FC<CustomModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  content,
  confirmText = '确定',
  cancelText = '取消',
  type = 'confirm'
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onClose();
    }, 300);
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    handleClose();
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'info':
        return 'ℹ️';
      default:
        return '❓';
    }
  };

  const getTypeClass = () => {
    switch (type) {
      case 'warning':
        return 'custom-modal-warning';
      case 'error':
        return 'custom-modal-error';
      case 'info':
        return 'custom-modal-info';
      default:
        return 'custom-modal-confirm';
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <div 
      className={`custom-modal-backdrop ${isVisible ? 'custom-modal-backdrop-visible' : ''}`}
      onClick={handleBackdropClick}
    >
      <div className={`custom-modal ${isVisible ? 'custom-modal-visible' : ''} ${getTypeClass()}`}>
        <div className="custom-modal-header">
          <div className="custom-modal-icon">{getIcon()}</div>
          <h3 className="custom-modal-title">{title}</h3>
        </div>
        
        <div className="custom-modal-content">
          <p>{content}</p>
        </div>
        
        <div className="custom-modal-footer">
          <button 
            className="custom-modal-button custom-modal-button-cancel"
            onClick={handleClose}
          >
            {cancelText}
          </button>
          {onConfirm && (
            <button 
              className="custom-modal-button custom-modal-button-confirm"
              onClick={handleConfirm}
            >
              {confirmText}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default CustomModal;
