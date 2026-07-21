import { useEffect, useMemo, useState } from "react";
import { Button, Card, Tag, Typography } from "antd";

/**
 * dtcoder 尝鲜版（首月）定价卡片。
 *
 * SSOT 合约（见 local-docs/dtcoder-9.9-trial-tasks.md）：
 *   plan_code        : trial-9.9-monthly
 *   原价锚点          : ¥99.00（划线展示）
 *   尝鲜价            : ¥9.9
 *   purchase_limit   : 1（每自然用户，限购1次）
 *   duration_days    : 30
 *
 * 该组件为受控展示组件：购买态由父层经 `hasPurchasedTrial` 传入，
 * 下单跳转入口由 `onPurchase` 回调触发，便于在不同宿主
 * （web 控制台 / Tauri 桌面端）接入真实下单链路。
 */

const { Text, Title } = Typography;

export const ORIGINAL_PRICE = 99;
export const TRIAL_PRICE = 9.9;
export const PURCHASE_LIMIT = 1;

export interface TrialCardProps {
  /** 当前用户是否已购买过尝鲜套餐；为 true 时按钮置灰显示“已享尝鲜价” */
  hasPurchasedTrial?: boolean;
  /** 点击购买下单入口回调（仅当未购且按钮可点时触发） */
  onPurchase?: () => void;
  /** 限时活动截止时间；不传则仅展示倒计时标签，不启动定时器 */
  deadline?: Date | string | number;
}

function formatRemaining(ms: number): string {
  if (ms <= 0) return "活动已结束";
  const totalSec = Math.floor(ms / 1000);
  const d = Math.floor(totalSec / 86400);
  const h = Math.floor((totalSec % 86400) / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return `${d}天 ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(
    s,
  ).padStart(2, "0")}`;
}

/** 限时倒计时：受控展示，未传 deadline 时不启动 interval，避免无谓渲染 */
export function Countdown({ deadline }: { deadline?: Date | string | number }) {
  const deadlineMs = useMemo(
    () => (deadline ? new Date(deadline).getTime() : null),
    [deadline],
  );
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (deadlineMs === null) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [deadlineMs]);

  if (deadlineMs === null) {
    return <Text type="secondary">限时倒计时：进行中</Text>;
  }
  return <Text type="warning">限时倒计时：{formatRemaining(deadlineMs - now)}</Text>;
}

export function TrialCard({
  hasPurchasedTrial,
  onPurchase,
  deadline,
}: TrialCardProps) {
  const purchased = Boolean(hasPurchasedTrial);

  return (
    <Card
      data-testid="trial-card"
      title={
        <Title level={4} style={{ margin: 0 }}>
          dtcoder 尝鲜版（首月）
        </Title>
      }
      extra={<Tag color="orange">限购{PURCHASE_LIMIT}次</Tag>}
      style={{ maxWidth: 360 }}
    >
      <div style={{ marginBottom: 8 }}>
        <Text delete type="secondary" style={{ marginRight: 12 }}>
          原价 ¥{ORIGINAL_PRICE}
        </Text>
        <Title
          level={3}
          style={{ display: "inline-block", margin: 0, color: "#ff4d4f" }}
        >
          尝鲜价 ¥{TRIAL_PRICE}
        </Title>
      </div>

      <Countdown deadline={deadline} />

      <div style={{ marginTop: 16 }}>
        <Button
          type="primary"
          danger
          disabled={purchased}
          onClick={purchased ? undefined : onPurchase}
          data-testid="trial-purchase-btn"
        >
          {purchased ? "已享尝鲜价" : `立即尝鲜 ¥${TRIAL_PRICE}`}
        </Button>
      </div>
    </Card>
  );
}

export default TrialCard;
