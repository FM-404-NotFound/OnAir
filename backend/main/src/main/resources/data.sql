INSERT IGNORE INTO user (fcm_token_id, phone_number, nickname, username, password, role, profile_path)
VALUES (NULL, '01062966409', 'test000', 'test000', '$2a$10$rSZOHWJi1HVyqt2DKwq0CewmxwG7YMqiRDz.62LfZYDyiDWsbtIFS',
        'ROLE_USER',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp'),
       (NULL, '01012345678', 'test111', 'test111', '$2a$10$rSZOHWJi1HVyqt2DKwq0CewmxwG7YMqiRDz.62LfZYDyiDWsbtIFS',
        'ROLE_USER',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp'),
       (NULL, '01023456789', 'test222', 'test222', '$2a$10$rSZOHWJi1HVyqt2DKwq0CewmxwG7YMqiRDz.62LfZYDyiDWsbtIFS',
        'ROLE_USER',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp'),
       (NULL, '01034567890', 'test333', 'test333', '$2a$10$rSZOHWJi1HVyqt2DKwq0CewmxwG7YMqiRDz.62LfZYDyiDWsbtIFS',
        'ROLE_USER',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp'),
       (NULL, '01045678901', 'test444', 'test444', '$2a$10$rSZOHWJi1HVyqt2DKwq0CewmxwG7YMqiRDz.62LfZYDyiDWsbtIFS',
        'ROLE_USER',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp'),
       (NULL, '01035974598', 'test777', 'test777', '$2a$10$yKgT3qj5M70CWowD3hOAuuES5.I6XPC/3ScnpzF59PxFhaOJswmsm',
        'ROLE_ADMIN',
        'https://i.namu.wiki/i/MD2QdCJ3W0DvXgUHI8u_dUbdo1y5H_jFBx5w0d8XhTPPbjO8kJeHcvVR6_hOsvHGxhhrKqlGkZvqk744wwYtvtWqyfs3OmXrJ-6B5zLP11S7LglORDjvx3BUS57PCAeRNDfKOCRyYH3VDMdENcMmig.webp');

-- fcm_token 테이블에 토큰 추가 및 매핑
INSERT IGNORE INTO fcm_token (id, value)
VALUES (1, 'sample_fcm_token_value');
SET @fcmTokenId = (SELECT id
                   FROM fcm_token
                   WHERE value = 'sample_fcm_token_value');
UPDATE `user`
SET fcm_token_id = @fcmTokenId
WHERE username = 'test777';