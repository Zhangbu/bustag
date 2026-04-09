% rebase('base.tpl', title='其他', path=path)

<div class="container">
 <div class="row py-3">
 <div class="col-10 offset-1 ">
    <div class="accordion" id="accordionExample">
  <div class="card">
    <div class="card-header" id="headingOne">
      <h2 class="mb-0">
        <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
          训练模型
        </button>
      </h2>
    </div>

    <div id="collapseOne" class="collapse show" aria-labelledby="headingOne" data-parent="#accordionExample">
        <div class="card-body">
        <h5 class="card-title">重新训练模型</h5>
        <p class="card-text">重新使用系统所有用户打标数据训练模型, 当打标数据增多后, 可以重新训练模型, 提高模型预测效果</p>
        <form action="/do-training" method="get" class="form-inline">
          <label class="mr-2" for="model">模型</label>
          <select class="form-control mr-2" id="model" name="model">
            % selected_name = selected_model if defined('selected_model') and selected_model else (model_metadata['model_name'] if defined('model_metadata') and model_metadata else '')
            % for option in model_options:
            <option value="{{option['name']}}" {{'selected' if option['name'] == selected_name else ''}}>{{option['label']}}</option>
            % end
          </select>
          <button type="submit" class="btn btn-primary">开始训练</button>
        </form>
        </div>

        % if defined('training_task_id') and training_task_id:
        <div class="card-body border-top">
          <h6>训练任务</h6>
          <p class="mb-1">任务ID: <code>{{training_task_id}}</code></p>
          % if training_task is None:
          <p class="text-muted mb-0">任务状态未知，可能已过期。可访问 <code>/task/{{training_task_id}}</code> 查看详情。</p>
          % else:
          <p class="mb-1">状态: <strong>{{training_task['status']}}</strong></p>
          % if training_task['status'] == 'failed' and training_task['error']:
          <p class="text-danger mb-1">失败原因: {{training_task['error']}}</p>
          % end
          % if training_task['status'] in ['pending', 'running']:
          <p class="text-muted mb-0">训练正在后台执行，刷新页面可查看最新状态。</p>
          % elif training_task['status'] == 'success':
          <p class="text-success mb-0">训练任务已完成，当前模型数据已刷新。</p>
          % end
          % end
        </div>
        % end

        <div class="card-header">
           <h6> 当前模型数据 </h6>
        </div>
        % if defined('error_msg') and error_msg is not None:
        <p class="card-text text-danger">{{error_msg}}</p>
        % end
        % if model_scores is not None:
        <ul class="list-group list-group-flush">
            % if defined('model_metadata') and model_metadata is not None:
            <li class="list-group-item">当前模型: {{model_metadata['model_label']}}</li>
            <li class="list-group-item">训练样本: {{model_metadata.get('train_size', '-')}} / 测试样本: {{model_metadata.get('test_size', '-')}}</li>
            % end
            <li class="list-group-item">准确率: {{model_scores['accuracy']}}</li>
            <li class="list-group-item">查准率: {{model_scores['precision']}}</li>
            <li class="list-group-item">覆盖率: {{model_scores['recall']}}</li>
            <li class="list-group-item">综合评分(越高越好): {{model_scores['f1']}}</li>
            % if 'cv_f1' in model_scores:
            <li class="list-group-item">交叉验证 F1: {{model_scores['cv_f1']}}</li>
            % end
            <li class="list-group-item">混淆矩阵: TP={{model_scores['tp']}}, FP={{model_scores['fp']}}, FN={{model_scores['fn']}}, TN={{model_scores['tn']}}</li>
        </ul>
        % else:
        <div class="card-body">
           还没有训练过模型.
        </div>
        % end
        </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header" id="headingTwo">
      <h2 class="mb-0">
        <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">

        </button>
      </h2>
    </div>
    <div id="collapseTwo" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionExample">
      <div class="card-body">
        Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et. Nihil anim keffiyeh helvetica, craft beer labore wes anderson cred nesciunt sapiente ea proident. Ad vegan excepteur butcher vice lomo. Leggings occaecat craft beer farm-to-table, raw denim aesthetic synth nesciunt you probably haven't heard of them accusamus labore sustainable VHS.
      </div>
    </div>
  </div>
 </div>
 </div>
</div>
</div>
