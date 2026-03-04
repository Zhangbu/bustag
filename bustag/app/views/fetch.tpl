% rebase('base.tpl', title='手动拉取', path=path, msg=msg, errmsg=errmsg)

<div class="container">
  <div class="row py-3">
    <div class="col-12">
      <h4>手动拉取数据</h4>
      <p class="text-muted">从网站手动拉取数据，可以指定页数范围和最大条数。</p>
    </div>
  </div>

  <div class="row">
    <div class="col-12 col-md-6">
      <div class="card">
        <div class="card-header">
          拉取参数设置
        </div>
        <div class="card-body">
          <form method="post" action="/fetch">
            <div class="form-group">
              <label for="start_page">起始页码</label>
              <input type="number" class="form-control" id="start_page" name="start_page" 
                     value="1" min="1" max="30" required>
              <small class="form-text text-muted">从第几页开始爬取（1-30）</small>
            </div>
            <div class="form-group">
              <label for="end_page">结束页码</label>
              <input type="number" class="form-control" id="end_page" name="end_page" 
                     value="1" min="1" max="30" required>
              <small class="form-text text-muted">爬取到第几页（1-30，不能超过起始页码太多）</small>
            </div>
            <div class="form-group">
              <label for="max_count">最大条数</label>
              <input type="number" class="form-control" id="max_count" name="max_count" 
                     value="100" min="1" max="1000" required>
              <small class="form-text text-muted">最多爬取多少条数据（1-1000）</small>
            </div>
            <button type="submit" name="submit" value="fetch" class="btn btn-primary">
              开始拉取
            </button>
          </form>
        </div>
      </div>
    </div>
    
    <div class="col-12 col-md-6">
      <div class="card">
        <div class="card-header">
          说明
        </div>
        <div class="card-body">
          <ul>
            <li><strong>起始页码</strong>：指定从哪一页开始爬取数据</li>
            <li><strong>结束页码</strong>：指定爬取到哪一页结束</li>
            <li><strong>最大条数</strong>：限制最多爬取的数据条数</li>
          </ul>
          <hr>
          <h6>注意事项：</h6>
          <ul class="text-muted">
            <li>页码范围为 1-30 页</li>
            <li>最大条数为 1-1000 条</li>
            <li>爬取可能需要一些时间，请耐心等待</li>
            <li>爬取完成后会自动执行推荐算法</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>