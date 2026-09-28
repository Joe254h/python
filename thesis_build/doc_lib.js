const D = require('docx');
const fs = require('fs');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,BorderStyle,
       AlignmentType,HeadingLevel,ImageRun,PageBreak,ShadingType,VerticalAlign,TabStopType}=D;

const FONT='Times New Roman', SZ=24, TSZ=20;      // 12pt body, 10pt tables
const BLACK='000000';
const CONTENT=9026;                                // A4 minus 1in margins, in DXA
const NONE={style:BorderStyle.NONE,size:0,color:'FFFFFF'};
const RULE={style:BorderStyle.SINGLE,size:6,color:BLACK};
const THIN={style:BorderStyle.SINGLE,size:4,color:BLACK};

// ---- text helpers ---------------------------------------------------------
function runs(text){
  // supports *italic* and **bold** inline
  const out=[]; const re=/(\*\*[^*]+\*\*|\*[^*]+\*)/g; let last=0,m;
  while((m=re.exec(text))!==null){
    if(m.index>last) out.push(new TextRun({text:text.slice(last,m.index),font:FONT,size:SZ,color:BLACK}));
    const t=m[0];
    if(t.startsWith('**')) out.push(new TextRun({text:t.slice(2,-2),font:FONT,size:SZ,color:BLACK,bold:true}));
    else out.push(new TextRun({text:t.slice(1,-1),font:FONT,size:SZ,color:BLACK,italics:true}));
    last=re.lastIndex;
  }
  if(last<text.length) out.push(new TextRun({text:text.slice(last),font:FONT,size:SZ,color:BLACK}));
  return out;
}
const P = (text,opt={})=> new Paragraph({
  children:runs(text),
  alignment:opt.align||AlignmentType.JUSTIFIED,
  spacing:{line:opt.line||360,after:opt.after===undefined?120:opt.after,before:opt.before||0},
  indent:opt.indent,
});
const H1 = t=> new Paragraph({
  children:[new TextRun({text:t,font:FONT,size:28,bold:true,color:BLACK})],
  heading:HeadingLevel.HEADING_1, alignment:AlignmentType.CENTER,
  spacing:{before:240,after:240,line:360}, pageBreakBefore:true});
const H2 = t=> new Paragraph({
  children:[new TextRun({text:t,font:FONT,size:26,bold:true,color:BLACK})],
  heading:HeadingLevel.HEADING_2, spacing:{before:280,after:140,line:360}});
const H3 = t=> new Paragraph({
  children:[new TextRun({text:t,font:FONT,size:24,bold:true,color:BLACK})],
  heading:HeadingLevel.HEADING_3, spacing:{before:240,after:120,line:360}});
const H4 = t=> new Paragraph({
  children:[new TextRun({text:t,font:FONT,size:24,bold:true,italics:true,color:BLACK})],
  heading:HeadingLevel.HEADING_4, spacing:{before:200,after:100,line:360}});

const BULLET = t=> new Paragraph({children:runs(t),numbering:{reference:'bul',level:0},
  alignment:AlignmentType.JUSTIFIED,spacing:{line:360,after:100}});
const NUMLIST = (t,ref)=> new Paragraph({children:runs(t),numbering:{reference:ref,level:0},
  alignment:AlignmentType.JUSTIFIED,spacing:{line:360,after:100}});

// ---- APA table ------------------------------------------------------------
function cellPara(text,{bold=false,italic=false,align=AlignmentType.LEFT,size=TSZ}={}){
  const lines=String(text).split('\n');
  return lines.map((ln,i)=> new Paragraph({
    children:[new TextRun({text:ln,font:FONT,size,bold,italics:italic,color:BLACK})],
    alignment:align, spacing:{line:240,after:i===lines.length-1?20:0,before:i===0?20:0}}));
}
function apaTable(spec){
  const nCol=spec.headers.length;
  const CSZ = spec.fontSize || (nCol>=8 ? 17 : TSZ);
  let w=spec.widths && spec.widths.length===nCol ? spec.widths.slice() : Array(nCol).fill(Math.floor(CONTENT/nCol));
  const s=w.reduce((a,b)=>a+b,0); w=w.map(x=>Math.round(x*CONTENT/s));
  w[nCol-1]+=CONTENT-w.reduce((a,b)=>a+b,0);

  const mk=(children,i,{top=NONE,bottom=NONE}={})=> new TableCell({
    children, width:{size:w[i],type:WidthType.DXA},
    borders:{top,bottom,left:NONE,right:NONE},
    margins:{top:30,bottom:30,left:60,right:60},
    verticalAlign:VerticalAlign.BOTTOM});

  const rows=[];
  // header row: rule above and below
  rows.push(new TableRow({tableHeader:true,children:spec.headers.map((h,i)=>
    mk(cellPara(h,{bold:true,size:CSZ,align:i===0?AlignmentType.LEFT:AlignmentType.CENTER}),i,{top:RULE,bottom:THIN}))}));

  spec.rows.forEach((r,ri)=>{
    const last = ri===spec.rows.length-1;
    const isBlock = String(r[0]).startsWith('__BLOCK__');
    const isTotal = String(r[0]).toLowerCase()==='total';
    if(isBlock){
      const lbl=String(r[0]).replace('__BLOCK__','');
      rows.push(new TableRow({children:[
        new TableCell({children:cellPara(lbl,{italic:true,size:CSZ}),
          columnSpan:nCol,width:{size:CONTENT,type:WidthType.DXA},
          borders:{top:NONE,bottom:NONE,left:NONE,right:NONE},
          margins:{top:90,bottom:30,left:90,right:90}})]}));
      return;
    }
    rows.push(new TableRow({children:r.map((c,i)=>
      mk(cellPara(c,{size:CSZ,align:i===0?AlignmentType.LEFT:AlignmentType.CENTER,bold:isTotal}),i,
         {bottom:last?RULE:NONE, top:isTotal?THIN:NONE}))}));
  });
  return new Table({rows,width:{size:CONTENT,type:WidthType.DXA},columnWidths:w,
    borders:{top:NONE,bottom:NONE,left:NONE,right:NONE,
             insideHorizontal:NONE,insideVertical:NONE}});
}
function tableBlock(spec){
  const out=[];
  if(spec.num!==null && spec.num!==undefined){
    out.push(new Paragraph({children:[new TextRun({text:`Table ${spec.num}`,font:FONT,size:SZ,bold:true,color:BLACK})],
      spacing:{before:240,after:0,line:240}}));
  }
  out.push(new Paragraph({children:[new TextRun({text:spec.title,font:FONT,size:SZ,
      bold:spec.num===null||spec.num===undefined, italics:!(spec.num===null||spec.num===undefined),
      color:BLACK})], spacing:{before:spec.num==null?240:0,after:120,line:240}}));
  out.push(apaTable(spec));
  if(spec.note){
    out.push(new Paragraph({
      children:[new TextRun({text:'Note. ',font:FONT,size:TSZ,italics:true,color:BLACK}),
                new TextRun({text:spec.note,font:FONT,size:TSZ,color:BLACK})],
      alignment:AlignmentType.JUSTIFIED, spacing:{before:100,after:240,line:240}}));
  }
  return out;
}
// ---- APA figure -----------------------------------------------------------
function figureBlock(num,title,file,note,sizes){
  const [pw,ph]=sizes[file];
  const W=600, Hh=Math.round(W*ph/pw);
  return [
    new Paragraph({children:[new TextRun({text:`Figure ${num}`,font:FONT,size:SZ,bold:true,color:BLACK})],
      spacing:{before:240,after:0,line:240}}),
    new Paragraph({children:[new TextRun({text:title,font:FONT,size:SZ,italics:true,color:BLACK})],
      spacing:{before:0,after:120,line:240}}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:100},
      children:[new ImageRun({type:'png',data:fs.readFileSync(`out/fig/${file}.png`),
        transformation:{width:W,height:Hh}})]}),
    new Paragraph({children:[new TextRun({text:'Note. ',font:FONT,size:TSZ,italics:true,color:BLACK}),
                             new TextRun({text:note,font:FONT,size:TSZ,color:BLACK})],
      alignment:AlignmentType.JUSTIFIED,spacing:{before:60,after:240,line:240}}),
  ];
}
module.exports={D,Document,Packer,Paragraph,TextRun,AlignmentType,PageBreak,
  P,H1,H2,H3,H4,BULLET,NUMLIST,tableBlock,figureBlock,apaTable,FONT,SZ,TSZ,BLACK,CONTENT,runs};
