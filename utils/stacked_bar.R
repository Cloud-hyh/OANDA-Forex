library(R.matlab)
library(ggplot2)

collect_pred_data = function(file_name) {
        pred.y = readMat(file_name)
        mat = pred.y$E
        pred.y = data.frame(mat)
        colnames(pred.y) = c('label','pred')
        pred.y$label = as.character(pred.y$label)
        pred.y$pred = as.character(pred.y$pred)
        return(pred.y)
}

plot_accuracy = function(file_name) {
        pred.y = collect_pred_data(file_name)
        ggplot(pred.y, aes(label, fill=pred)) + geom_bar() 
}

plot_error = function(file_name) {
        pred.y = collect_pred_data(file_name)
        errors.y = pred.y[pred.y$label!=pred.y$pred,]
        str(errors.y)
        ggplot(errors.y, aes(label, fill=pred)) + geom_bar() 
}




