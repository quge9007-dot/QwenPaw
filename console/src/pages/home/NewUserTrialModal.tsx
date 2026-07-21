import { useEffect, useState } from "react";
import { Button, Modal, Typography } from "antd";

/**
 * 新用户首登引导弹窗：引导用户前往 dtcoder 尝鲜价（¥9.9/首月）。
 *
 * SSOT 生命周期：注册 → 引导 → 购买 9.9 → ...
 * 该弹窗在新用户首次登录时展示，提供“立即抢尝鲜价”入口，
 * 由 `onGoToTrial` 回调跳转至定价页 / 下单链路。
 *
 * 受控展示组件：
 *   - `isFirstLogin` 由父层（鉴权/用户档案）判定后传入，决定首登是否自动弹出；
 *   - `open` 可显式覆盖可见性（便于父层按需控制）；
 *   - 关闭或点击“立即抢尝鲜价”均会回调宿主，由宿主完成路由跳转与埋点（trial_view/trial_purchase）。
 */

const { Title, Paragraph, Text } = Typography;

export interface NewUserTrialModalProps {
  /** 是否为新用户首次登录；为 true 时弹窗自动展示 */
  isFirstLogin?: boolean;
  /** 显式可见性控制，优先于 isFirstLogin 推导的内部态 */
  open?: boolean;
  /** 点击“立即抢尝鲜价”回调（跳转下单/定价页入口） */
  onGoToTrial?: () => void;
  /** 关闭回调 */
  onClose?: () => void;
}

export function NewUserTrialModal({
  isFirstLogin = false,
  open,
  onGoToTrial,
  onClose,
}: NewUserTrialModalProps) {
  const [internalOpen, setInternalOpen] = useState<boolean>(isFirstLogin);

  useEffect(() => {
    setInternalOpen(isFirstLogin);
  }, [isFirstLogin]);

  const isOpen = open ?? internalOpen;

  const handleClose = () => {
    setInternalOpen(false);
    onClose?.();
  };

  const handleGoToTrial = () => {
    onGoToTrial?.();
    handleClose();
  };

  return (
    <Modal
      data-testid="new-user-trial-modal"
      open={isOpen}
      onCancel={handleClose}
      footer={[
        <Button key="later" onClick={handleClose}>
          稍后再说
        </Button>,
        <Button key="go" type="primary" danger onClick={handleGoToTrial}>
          立即抢尝鲜价
        </Button>,
      ]}
    >
      <Title level={4}>新用户专享福利</Title>
      <Paragraph>
        <Text strong>dtcoder 尝鲜版</Text>：原价 ¥99，首月仅需
        <Text type="danger" strong>
          {" "}¥9.9
        </Text>
        ，限购 1 次。
      </Paragraph>
      <Paragraph type="secondary">
        限时活动，到期恢复原价。立即体验旗舰模型权益，30 天后到期自动降级免费版。
      </Paragraph>
    </Modal>
  );
}

export default NewUserTrialModal;
