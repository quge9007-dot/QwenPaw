package com.qwenpaw.usermanagement.model.dto;

import java.util.List;

/**
 * 标签匹配结果对象
 */
public class MatchResultDTO {

    private long total;
    private List<UserDTO> userList;
    private String matchType;

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

    public List<UserDTO> getUserList() {
        return userList;
    }

    public void setUserList(List<UserDTO> userList) {
        this.userList = userList;
    }

    public String getMatchType() {
        return matchType;
    }

    public void setMatchType(String matchType) {
        this.matchType = matchType;
    }
}
