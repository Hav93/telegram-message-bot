import React, { useState, useEffect } from 'react';
import { Modal, Steps, Form, Input, Button, message, Alert, Space } from 'antd';
import { LoginOutlined, SafetyCertificateOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { clientsApi } from '../../services/clients';

const { Step } = Steps;

interface ClientLoginModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  clientId: string;
  clientType: 'user' | 'bot';
}

export const ClientLoginModal: React.FC<ClientLoginModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  clientId,
  clientType
}) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [loginStep, setLoginStep] = useState<'send_code' | 'submit_code' | 'submit_password' | 'completed'>('send_code');

  // 当模态框打开时重置状态
  useEffect(() => {
    if (visible) {
      console.log('🔄 模态框打开，重置登录状态');
      setCurrentStep(0);
      setLoginStep('send_code');
      form.resetFields();
    }
  }, [visible, form]);

  const loginMutation = useMutation({
    mutationFn: (data: any) => {
      console.log('🚀 发起登录API请求:', { clientId, data });
      return clientsApi.clientLogin(clientId, data);
    },
    onSuccess: (data) => {
      console.log('✅ 登录API响应成功:', data);
      console.log('🔍 响应数据类型:', typeof data, data);
      console.log('🔍 当前登录步骤:', loginStep);
      
      if (data.success) {
        console.log('✅ 登录成功，下一步:', data.step);
        if (data.step === 'waiting_code') {
          console.log('📱 设置为验证码输入步骤');
          setCurrentStep(1);
          setLoginStep('submit_code');
          message.success(data.message || '验证码已发送');
        } else if (data.step === 'waiting_password') {
          console.log('🔐 设置为密码输入步骤');
          setCurrentStep(2);
          setLoginStep('submit_password');
          message.info(data.message || '需要输入二步验证密码');
        } else if (data.step === 'completed') {
          console.log('🎉 登录完成');
          setCurrentStep(3);
          setLoginStep('completed');
          message.success(data.message || '登录成功');
          setTimeout(() => {
            onSuccess();
            handleReset();
          }, 2000);
        }
      } else {
        console.error('❌ 登录失败:', data.message);
        message.error(data.message || '登录失败');
      }
    },
    onError: (error: any) => {
      console.error('❌ 登录API请求失败:', error);
      console.error('❌ 错误详情:', error.response?.data || error.message);
      message.error(error.response?.data?.message || error.message || '登录失败');
    }
  });

  const handleSendCode = () => {
    console.log('🔔 用户点击发送验证码按钮');
    console.log('🔍 当前客户端ID:', clientId);
    console.log('🔍 当前登录步骤:', loginStep);
    loginMutation.mutate({ step: 'send_code' });
  };

  const handleSubmitCode = (values: { code: string }) => {
    loginMutation.mutate({ 
      step: 'submit_code', 
      code: values.code 
    });
  };

  const handleSubmitPassword = (values: { password: string }) => {
    loginMutation.mutate({ 
      step: 'submit_password', 
      password: values.password 
    });
  };

  const handleReset = () => {
    setCurrentStep(0);
    setLoginStep('send_code');
    form.resetFields();
  };

  const handleCancel = () => {
    handleReset();
    onCancel();
  };

  const steps = [
    {
      title: '发送验证码',
      icon: <LoginOutlined />,
      description: '向手机号发送验证码'
    },
    {
      title: '输入验证码',
      icon: <SafetyCertificateOutlined />,
      description: '输入收到的6位验证码'
    },
    {
      title: '二步验证',
      icon: <SafetyCertificateOutlined />,
      description: '输入二步验证密码（如果需要）'
    },
    {
      title: '登录完成',
      icon: <CheckCircleOutlined />,
      description: '用户客户端登录成功'
    }
  ];

  const renderStepContent = () => {
    console.log('Current loginStep:', loginStep); // 调试日志
    switch (loginStep) {
      case 'send_code':
        return (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Alert
              message="开始登录流程"
              description={`即将为用户客户端 ${clientId} 发送验证码到配置的手机号`}
              type="info"
              showIcon
              style={{ marginBottom: 20 }}
            />
            <Button 
              type="primary" 
              size="large"
              loading={loginMutation.isPending}
              onClick={handleSendCode}
              icon={<LoginOutlined />}
            >
              发送验证码
            </Button>
          </div>
        );

      case 'submit_code':
        return (
          <Form
            form={form}
            onFinish={handleSubmitCode}
            layout="vertical"
            style={{ padding: '20px 0' }}
          >
            <Alert
              message="验证码已发送"
              description="请查看手机短信，输入收到的6位验证码"
              type="success"
              showIcon
              style={{ marginBottom: 20 }}
            />
            
            <Form.Item
              name="code"
              label="验证码"
              rules={[
                { required: true, message: '请输入验证码' },
                { pattern: /^\d{5,6}$/, message: '请输入5-6位数字验证码' }
              ]}
            >
              <Input
                placeholder="输入6位验证码"
                maxLength={6}
                style={{ fontSize: '18px', textAlign: 'center', letterSpacing: '4px' }}
              />
            </Form.Item>
            
            <Form.Item style={{ textAlign: 'center', marginBottom: 0 }}>
              <Space>
                <Button onClick={handleCancel}>
                  取消
                </Button>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={loginMutation.isPending}
                >
                  验证登录
                </Button>
              </Space>
            </Form.Item>
          </Form>
        );

      case 'submit_password':
        return (
          <Form
            form={form}
            onFinish={handleSubmitPassword}
            layout="vertical"
            style={{ padding: '20px 0' }}
          >
            <Alert
              message="需要二步验证"
              description="您的账户启用了二步验证，请输入验证密码"
              type="warning"
              showIcon
              style={{ marginBottom: 20 }}
            />
            
            <Form.Item
              name="password"
              label="二步验证密码"
              rules={[{ required: true, message: '请输入二步验证密码' }]}
            >
              <Input.Password placeholder="输入二步验证密码" />
            </Form.Item>
            
            <Form.Item style={{ textAlign: 'center', marginBottom: 0 }}>
              <Space>
                <Button onClick={handleCancel}>
                  取消
                </Button>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={loginMutation.isPending}
                >
                  完成登录
                </Button>
              </Space>
            </Form.Item>
          </Form>
        );

      case 'completed':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
            <h3>登录成功！</h3>
            <p style={{ color: '#666' }}>用户客户端已成功连接到Telegram</p>
          </div>
        );

      default:
        return null;
    }
  };

  if (clientType !== 'user') {
    return null;
  }

  return (
    <Modal
      title={`用户客户端登录 - ${clientId}`}
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
      destroyOnClose
    >
      <Steps current={currentStep} style={{ marginBottom: 30 }}>
        {steps.map((step, index) => (
          <Step 
            key={index}
            title={step.title}
            description={step.description}
            icon={step.icon}
          />
        ))}
      </Steps>
      
      {renderStepContent()}
    </Modal>
  );
};
