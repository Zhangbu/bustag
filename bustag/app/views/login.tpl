<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="shortcut icon" type="image/ico" href="/static/images/favicon.ico"/>
    <link rel="stylesheet" type="text/css" href="/static/css/bootstrap.min.css">
    <title>登录 - Bustag</title>
    <style>
      body {
        background-color: #f5f5f5;
      }
      .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      }
      .login-container h2 {
        text-align: center;
        margin-bottom: 30px;
        color: #333;
      }
      .login-container .logo {
        text-align: center;
        margin-bottom: 20px;
      }
      .login-container .logo img {
        width: 120px;
      }
      .btn-login {
        width: 100%;
        padding: 10px;
      }
      .alert {
        margin-bottom: 20px;
      }
    </style>
  </head>
  <body>
    <div class="login-container">
      <div class="logo">
        <img src="/static/images/logo.png" alt="Bustag">
      </div>
      <h2>用户登录</h2>
      % if defined('error') and error:
      <div class="alert alert-danger" role="alert">
        {{error}}
      </div>
      % end
      <form method="POST" action="/login">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" class="form-control" id="username" name="username" required autofocus>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" class="form-control" id="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary btn-login">登录</button>
      </form>
      <div class="text-center mt-3">
        <small class="text-muted">默认账号: admin / admin123</small>
      </div>
    </div>
    <script src="/static/js/jquery.min.js"></script>
    <script src="/static/js/bootstrap.min.js"></script>
  </body>
</html>