package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.model.dto.UserDTO;
import com.qwenpaw.usermanagement.model.request.CreateUserRequest;
import com.qwenpaw.usermanagement.model.request.UpdateUserRequest;
import com.qwenpaw.usermanagement.common.model.PageResult;
import com.qwenpaw.usermanagement.service.UserService;
import org.springframework.web.bind.annotation.*;

/**
 * 用户管理控制器
 */
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping
    public UserDTO createUser(@RequestBody CreateUserRequest request) {
        return userService.createUser(request);
    }

    @PutMapping("/{userId}")
    public UserDTO updateUser(@PathVariable String userId, @RequestBody UpdateUserRequest request) {
        return userService.updateUser(request);
    }

    @DeleteMapping("/{userId}")
    public boolean deleteUser(@PathVariable String userId) {
        return userService.deleteUser(userId);
    }

    @GetMapping("/{userId}")
    public UserDTO getUserById(@PathVariable String userId) {
        return userService.getUserById(userId);
    }

    @GetMapping
    public PageResult<UserDTO> listUsers(
            @RequestParam(required = false) Integer status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize) {
        return userService.listUsers(status, page, pageSize);
    }

    @PostMapping("/{userId}/tags")
    public boolean bindTag(@PathVariable String userId, @RequestParam String tagId) {
        return userService.bindTag(userId, tagId);
    }

    @DeleteMapping("/{userId}/tags/{tagId}")
    public boolean unbindTag(@PathVariable String userId, @PathVariable String tagId) {
        return userService.unbindTag(userId, tagId);
    }
}
