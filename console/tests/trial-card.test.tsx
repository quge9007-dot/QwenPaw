import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TrialCard } from "@/pages/pricing/TrialCard";
import { NewUserTrialModal } from "@/pages/home/NewUserTrialModal";

/**
 * Task 6 测试：dtcoder 9.9 尝鲜价套餐 — 用户侧展示与购买入口
 * 3 用例：卡片渲染 / 限购置灰 / 弹窗触发
 */

describe("TrialCard", () => {
  it("renders trial card with struck ¥99, trial ¥9.9 and limit tag", () => {
    render(<TrialCard />);

    expect(screen.getByTestId("trial-card")).toBeInTheDocument();
    // 划线原价 ¥99
    expect(screen.getByText(/原价 ¥99/)).toBeInTheDocument();
    // 尝鲜价 ¥9.9
    expect(screen.getByText(/尝鲜价 ¥9.9/)).toBeInTheDocument();
    // 限购1次标签
    expect(screen.getByText(/限购1次/)).toBeInTheDocument();
  });

  it("disables purchase button and shows 已享尝鲜价 when hasPurchasedTrial=true", () => {
    const onPurchase = vi.fn();
    render(<TrialCard hasPurchasedTrial onPurchase={onPurchase} />);

    const btn = screen.getByTestId("trial-purchase-btn") as HTMLButtonElement;
    expect(btn).toBeDisabled();
    expect(btn).toHaveTextContent("已享尝鲜价");
  });

  it("enables purchase and triggers onPurchase (下单入口) when not purchased", () => {
    const onPurchase = vi.fn();
    render(<TrialCard onPurchase={onPurchase} />);

    const btn = screen.getByTestId("trial-purchase-btn") as HTMLButtonElement;
    expect(btn).not.toBeDisabled();
    fireEvent.click(btn);
    expect(onPurchase).toHaveBeenCalledTimes(1);
  });
});

describe("NewUserTrialModal", () => {
  it("shows on first login (首登显示) and guides to trial price", () => {
    render(<NewUserTrialModal isFirstLogin />);

    expect(screen.getByTestId("new-user-trial-modal")).toBeInTheDocument();
    expect(screen.getByText("新用户专享福利")).toBeInTheDocument();
    expect(screen.getByText(/¥9.9/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "立即抢尝鲜价" }),
    ).toBeInTheDocument();
  });

  it("does not show when not first login", () => {
    render(<NewUserTrialModal isFirstLogin={false} />);
    expect(screen.queryByText("新用户专享福利")).not.toBeInTheDocument();
  });
});
