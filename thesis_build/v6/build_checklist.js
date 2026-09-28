const D=require('docx'); const fs=require('fs');
const L=require('../doc_lib.js');
const {Document,Packer,AlignmentType}=D;
const {P,H1,H2,tableBlock}=L;
const A=require('./checklist.json');
const children=[];
for(const b of A){
  switch(b.k){
    case 'h1': children.push(H1(b.t)); break;
    case 'h2': children.push(H2(b.t)); break;
    case 'p':  children.push(P(b.t)); break;
    case 'rawtable':
      children.push(...tableBlock({num:null, title:b.title, headers:b.headers,
                                   rows:b.rows, widths:b.widths, fontSize:19}));
      break;
  }
}
const doc=new Document({
  creator:'Mercy Sangura', title:'Revision Checklist',
  styles:{default:{document:{run:{font:'Times New Roman',size:24,color:'000000'},
                             paragraph:{spacing:{line:300}}}}},
  sections:[{properties:{page:{size:{width:11906,height:16838},
    margin:{top:1134,right:1134,bottom:1134,left:1134}}}, children}],
});
Packer.toBuffer(doc).then(b=>{
  fs.writeFileSync('v6/Revision_Checklist.docx',b);
  console.log('written', (b.length/1024).toFixed(0)+' KB');
});
